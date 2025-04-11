"""Defines LangChain tools for interacting with the CRM system."""

import logging
from typing import Dict, Any, Optional, List

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.integrations.crm.factory import get_crm_adapter

logger = logging.getLogger(__name__)

# Initialize the CRM adapter using the factory
_crm_adapter = get_crm_adapter()
if _crm_adapter is None:
    logger.error(
        "Не удалось инициализировать адаптер CRM. Инструменты CRM не будут работать. "
        "Проверьте настройки конфигурации CRM"
    )


class CrmCustomerInfoInput(BaseModel):
    """Структура входных данных для инструмента get_crm_customer_info."""
    customer_id: str = Field(
        description="Уникальный идентификатор (ID) клиента в CRM системе компании АРЕАЛ."
    )


@tool(args_schema=CrmCustomerInfoInput)
def get_crm_customer_info(customer_id: str) -> str:
    """
    **Назначение:** Получает информацию о клиенте компании "АРЕАЛ" из CRM по его ID.
    **Данные:** Возвращает сводку, включающую: Название организации/Имя, Email, Телефон, количество связанных заявок/сделок, дату создания.
    **Когда использовать:** Применяй этот инструмент, если пользователь (обычно сотрудник "АРЕАЛ") запрашивает информацию о КОНКРЕТНОМ СУЩЕСТВУЮЩЕМ клиенте, и его ID известен или может быть точно определен из запроса. Не используй для поиска клиентов по имени или другим параметрам.
    **Пример запроса пользователя:** "Найди информацию по клиенту с ID 55123", "Что известно о клиенте 55123 в CRM?"
    **Результат:** Строка с основной информацией о клиенте или сообщение об ошибке.
    """
    if _crm_adapter is None:
        logger.warning("Инструмент CRM вызван, но адаптер недоступен.")
        return "Функциональность CRM недоступна из-за ошибки конфигурации."
    
    try:
        result = _crm_adapter.get_customer_info(customer_id=customer_id)
        
        # Handle error string result
        if isinstance(result, str):
            logger.info(f"CRM вернул сообщение об ошибке: {result}")
            return result
        
        # Handle None result (should not happen if adapter is configured, but for safety)
        if result is None:
            return "Информация о клиенте не была получена из CRM."
            
        # Parse the result dictionary into a user-friendly string summary
        try:
            return _format_customer_info(result)
        except Exception as format_err:
            logger.error(f"Ошибка форматирования информации о клиенте: {format_err}", exc_info=True)
            # Return a basic summary if formatting fails
            return f"Клиент найден (ID: {customer_id}), но не удалось отформатировать детали: {str(format_err)}"
    
    except Exception as e:
        logger.error(f"Непредвиденная ошибка в инструменте get_crm_customer_info: {e}", exc_info=True)
        return f"Произошла непредвиденная ошибка при обработке запроса к CRM: {type(e).__name__}."


def _format_customer_info(customer_data: Dict[str, Any]) -> str:
    """
    Форматирует сырые данные о клиенте из CRM в читаемую строку-сводку.
    Предназначена для использования внутри инструмента get_crm_customer_info.

    Args:
        customer_data: Словарь с данными о клиенте, полученный от CRM адаптера.

    Returns:
        Строка с отформатированной информацией о клиенте.
    """
    # Get basic info (assuming AmoCRM structure, but could be extended)
    customer_id = customer_data.get('id', 'Неизвестно')
    name = customer_data.get('name', 'Неизвестно')
    
    # Initialize summary parts
    summary_parts = [f"Клиент найден: ID={customer_id}, Имя/Название='{name}'"]
    
    # Extract email and phone from custom fields if available
    # AmoCRM typically stores these in custom_fields_values array
    custom_fields = customer_data.get('custom_fields_values', [])
    
    email = _extract_custom_field_value(custom_fields, ['EMAIL', 'EMAILADDRESS', 'email'])
    if email:
        summary_parts.append(f"Email='{email}'")
        
    phone = _extract_custom_field_value(custom_fields, ['PHONE', 'TELEPHONE', 'phone'])
    if phone:
        summary_parts.append(f"Phone='{phone}'")
    
    # Check for embedded/linked entities
    embedded = customer_data.get('_embedded', {})
    
    # Count leads if available
    leads = embedded.get('leads', [])
    if leads:
        lead_count = len(leads)
        summary_parts.append(f"Связанные лиды: {lead_count}")
    
    # Add created_at/updated_at if available
    created_at = customer_data.get('created_at')
    if created_at:
        # Convert timestamp if needed
        summary_parts.append(f"Создан: {created_at}")
    
    # Join all parts with commas
    return ", ".join(summary_parts)


def _extract_custom_field_value(
    custom_fields: List[Dict[str, Any]],
    possible_field_codes: List[str]
) -> Optional[str]:
    """
    Вспомогательная функция для извлечения значения из списка кастомных полей AmoCRM.
    Ищет поле по одному из возможных кодов (регистронезависимо) и возвращает первое найденное значение.

    Args:
        custom_fields: Список словарей кастомных полей из ответа API AmoCRM.
        possible_field_codes: Список возможных кодов поля (например, ['EMAIL', 'Phone']).

    Returns:
        Найденное значение поля в виде строки или None, если поле не найдено или пустое.
    """
    if not custom_fields:
        return None
        
    # Lower case all possible codes for case-insensitive matching
    possible_codes_lower = [code.lower() for code in possible_field_codes]
    
    for field in custom_fields:
        field_code = field.get('field_code', '').lower()
        field_name = field.get('field_name', '').lower()
        
        # Check if this field matches any of our target codes
        if field_code in possible_codes_lower or field_name in possible_codes_lower:
            # AmoCRM typically has values as a list with the first item containing the value
            values = field.get('values', [])
            if values and isinstance(values, list) and len(values) > 0:
                return values[0].get('value')
    
    return None 