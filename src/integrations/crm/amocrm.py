"""Concrete implementation of the CRMWrapper for AmoCRM."""

import logging
import requests
from typing import Dict, Any, Optional

from .base import CRMWrapper
from src.config.settings import settings

logger = logging.getLogger(__name__)


class AmoCRMAdapter(CRMWrapper):
    """Adapter for interacting with the AmoCRM v4 API."""

    def __init__(self) -> None:
        """Initializes the AmoCRM adapter, storing credentials.

        Logs a warning if essential configuration (API key, base URL) is missing.
        """
        self.api_key: Optional[str] = settings.AMO_CRM_API_KEY
        self.base_url: Optional[str] = settings.AMO_CRM_BASE_URL
        self.is_configured: bool = bool(self.api_key and self.base_url)

        if not self.is_configured:
            logger.warning(
                "AmoCRMAdapter инициализирован, но отсутствует API ключ или Base URL в настройках. "
                "Операции с CRM, скорее всего, не будут работать."
            )
        else:
            # Remove trailing slash from base_url if present
            if self.base_url.endswith('/'):
                self.base_url = self.base_url[:-1]
            logger.info("AmoCRMAdapter успешно инициализирован.")

    @property
    def headers(self) -> Dict[str, str]:
        """Constructs the necessary authentication headers."""
        if not self.api_key:
            # This should ideally not be reached if is_configured is checked,
            # but provides an extra layer of safety.
            return {}
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def get_customer_info(self, customer_id: str) -> Optional[Dict[str, Any]] | str:
        """
        Fetches contact information from AmoCRM using the v4 API.

        Args:
            customer_id: The ID of the contact in AmoCRM.

        Returns:
            A dictionary containing contact data if successful,
            an error message string if not found or an API error occurs,
            or None if the adapter is not configured.
        """
        if not self.is_configured:
            logger.error("AmoCRMAdapter не настроен. Невозможно получить информацию о клиенте.")
            return None # Return None to indicate configuration issue

        # Assert base_url is not None due to is_configured check
        assert self.base_url is not None

        # Consider adding query parameters like ?with=leads,contacts if needed
        api_url = f"{self.base_url}/api/v4/contacts/{customer_id}"

        try:
            response = requests.get(api_url, headers=self.headers, timeout=15)
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)

            customer_data = response.json()
            logger.info(f"Успешно получена информация для контакта AmoCRM с ID: {customer_id}")
            return customer_data

        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code
            if status_code == 401: # Unauthorized
                 logger.error(
                    f"Ошибка API AmoCRM ({status_code}): Не авторизован. Проверьте API ключ.",
                    exc_info=True
                 )
                 return "Ошибка CRM API: Ошибка аутентификации."
            elif status_code == 404: # Not Found
                logger.warning(f"Контакт AmoCRM с ID {customer_id} не найден (404).", exc_info=False)
                return f"Ошибка CRM: Клиент с ID {customer_id} не найден."
            else:
                logger.error(
                    f"Ошибка HTTP API AmoCRM ({status_code}): {http_err.response.text}",
                    exc_info=True
                )
                return f"Ошибка CRM API: Получен статус {status_code}."

        except requests.exceptions.Timeout:
            logger.error(f"Запрос к API AmoCRM истек по времени для контакта с ID {customer_id}.", exc_info=True)
            return "Ошибка подключения к CRM: Истекло время ожидания запроса."

        except requests.exceptions.RequestException as req_err:
            logger.error(f"Запрос к API AmoCRM не выполнен: {req_err}", exc_info=True)
            return f"Ошибка подключения к CRM: {req_err}."

        except Exception as e:
            # Catch unexpected errors during request or JSON parsing
            logger.error(f"Непредвиденная ошибка при получении данных контакта AmoCRM {customer_id}: {e}", exc_info=True)
            return f"Ошибка CRM: Произошла непредвиденная ошибка ({type(e).__name__})."

    # --- Implement other methods like create_lead here ---

# </rewritten_file> 