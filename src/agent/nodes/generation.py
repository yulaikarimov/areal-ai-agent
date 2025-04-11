"""Node for generating responses using the LLM, potentially calling tools."""

import logging
from typing import Dict, List, Optional, Any

from langchain_core.messages import (AIMessage, BaseMessage, HumanMessage,
                                   SystemMessage)

from src.agent.state import AgentState
from src.config.llm_factory import get_chat_model
# Import the specific tool function(s) decorated with @tool
from src.tools.crm_tools import get_crm_customer_info

logger = logging.getLogger(__name__)

# --- Module Level Initialization --- 

# Initialize chat model
_chat_model = None
_LLM_AVAILABLE = False
try:
    _chat_model = get_chat_model()
    _LLM_AVAILABLE = _chat_model is not None
    if not _LLM_AVAILABLE:
         logger.error(
            "Не удалось инициализировать языковую модель. Узел генерации будет нефункционален."
        )
except ValueError as e:
    logger.error(f"Не удалось инициализировать языковую модель: {e}", exc_info=True)
except Exception as e: # Catch any other unexpected errors
    logger.error(f"Непредвиденная ошибка при инициализации языковой модели: {e}", exc_info=True)

# Define the list of tools available to the LLM
# Ensure these are functions decorated with @tool
_tools_list = [get_crm_customer_info]

async def generator(state: AgentState) -> dict[str, Any]:
    """Invokes the LLM to generate a response based on the current state (messages + retrieved docs).
    Also handles potential tool calls requested by the LLM.

    Args:
        state: The current state of the agent graph.

    Returns:
        A dictionary containing updates for 'generation', 'messages',
        and 'tool_calls' keys in the state.
    """
    logger.info("---NODE: generator---")
    # --- BEGIN Force DEBUG Level for Diagnosis ---
    logger.setLevel(logging.DEBUG)
    # --- END Force DEBUG Level for Diagnosis ---
    generation_text: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None # Default to None

    # Check prerequisites
    if not _LLM_AVAILABLE or _chat_model is None:
        logger.error("Языковая модель недоступна. Невозможно сгенерировать ответ.")
        # Update state to reflect the error - Append an AIMessage with error
        error_message = AIMessage(content="Ошибка: Языковая модель недоступна.")
        updated_messages = state['messages'] + [error_message]
        return {"messages": [error_message]}

    messages: List[BaseMessage] = state['messages']
    retrieved_docs: Optional[List[str]] = state.get('retrieved_docs')

    # --- BEGIN ADDED LOGGING ---
    logger.debug(f"Generator node received retrieved_docs: {retrieved_docs}")
    # --- END ADDED LOGGING ---

    # 1. Construct Prompt Messages
    prompt_messages: List[BaseMessage] = []

    # Define formatted_docs before using it in the system prompt
    formatted_docs = "Нет контекстных документов."
    if retrieved_docs:
        context_str = "\n\n--- Context Documents ---\n"
        for i, doc in enumerate(retrieved_docs):
            context_str += f"\nDocument {i+1}:\n{doc}\n---"
        formatted_docs = context_str # Store the formatted string

        # --- BEGIN ADDED LOGGING --- # Keep this logging
        logger.debug(f"Formatted context string for prompt: {formatted_docs[:500]}...") # Log first 500 chars
        # --- END ADDED LOGGING --- 
    else:
        logger.info("Не найдены документы для добавления в контекст запроса.")

    # System Message (Role, Capabilities, Instructions)
    system_prompt_template = (
    """Ты — проактивный и компетентный ИИ-ассистент компании "АРЕАЛ". Твоя роль — быть полезным гидом в мире экологических услуг и обращения с отходами для наших клиентов и эффективным помощником для сотрудников.

**Главный принцип: точность и опора на факты.** Используй предоставленные КОНТЕКСТНЫЕ ДОКУМЕНТЫ как единственный источник фактической информации об услугах, технологиях, лицензиях "АРЕАЛ". Если данных нет — не гадай, а честно скажи об этом и предложи связаться со специалистом (8 800 555 90 57).

**Стиль общения: ... ВАЖНО: Твой ответ будет показан пользователю в простом текстовом мессенджере (например, Telegram). Поэтому КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать ЛЮБУЮ Markdown разметку в твоем ответе, включая: звездочки для списков (*), двойные звездочки для выделения (**полужирный**), одинарные звездочки (*курсив*), обратные кавычки (`код`), заголовки (#). Используй только обычный текст, переносы строк и абзацы.**

**Взаимодействие:**
*   **Слушай внимательно:** Старайся полностью понять запрос пользователя.
*   **Уточняй:** Если запрос неполный, неоднозначный, или если нужна дополнительная информация для действия (оформление заявки, поиск клиента в CRM), **обязательно задай вежливые уточняющие вопросы**. Не приступай к действию, не убедившись, что все понял правильно.
*   **Используй инструменты:** Применяй CRM-инструменты (`get_crm_customer_info`, `create_crm_lead`) только по назначению и при наличии достаточной информации.
*   **Оформляй заявки:** Помогай пользователям инициировать заявки, собирая нужные данные (ФИО, контакты, суть) и передавая их в CRM. **Помни:** финальное подтверждение, цены и сроки дает только менеджер. Твоя задача – принять запрос в работу. Сообщай клиенту: "Спасибо, я зафиксировал ваш запрос. Наш менеджер свяжется с вами в ближайшее время для уточнения деталей и подготовки коммерческого предложения."
*   **Используй речевые модули:** Если найденный контекст содержит подходящий речевой модуль (например, для ответа на возражение), используй его основные идеи и стиль, но адаптируй под конкретный диалог. Не копируй дословно.
*   **Важно: Не начинай свой ответ с приветствия ("Здравствуйте", "Добрый день" и т.п.), если это не самое первое сообщение в диалоге (т.е. если история сообщений уже содержит предыдущие реплики).**

**Важные "НЕ":** Не гарантируй цены/сроки, не консультируй по юридическим тонкостям сверх базы знаний, не подтверждай прием отходов вне лицензии, не раскрывай конфиденциальную информацию.

КОНТЕКСТНЫЕ ДОКУМЕНТЫ (если найдены):
---
{formatted_docs}
---
"""
    )
    # Now format the system prompt with the defined formatted_docs
    prompt_messages.append(SystemMessage(content=system_prompt_template.format(formatted_docs=formatted_docs)))

    # Add existing conversation history loaded by the checkpointer
    # Ensure messages is a list before extending
    history = state.get('messages', [])
    if isinstance(history, list):
        prompt_messages.extend(history)
    else:
        logger.warning(f"'messages' in state is not a list: {type(history)}. Skipping history.")

    # Add the *current* user input as the last message
    current_input = state.get('input')
    if current_input:
        prompt_messages.append(HumanMessage(content=current_input))
    else:
        logger.warning("'input' key is missing or empty in the state. LLM might lack current context.")

    # logger.debug(f"Сообщения для запроса подготовлены (количество: {len(prompt_messages)}). Последнее сообщение: {prompt_messages[-1].content[:100]}...")
    # Improved logging for clarity
    logger.info(
        f"Prompt messages constructed. Total: {len(prompt_messages)}. "
        f"Includes History: {len(history) > 0}. "
        f"Last Message Type: {type(prompt_messages[-1]).__name__ if prompt_messages else 'None'}. "
        f"Last Message Content: {prompt_messages[-1].content[:100] if prompt_messages else 'None'}..."
    )

    # 2. Bind Tools and Invoke LLM
    try:
        # Bind the tools to the LLM instance for this call
        llm_with_tools = _chat_model.bind_tools(_tools_list)

        # --- BEGIN ADDED DEBUG LOGGING --- 
        actual_model_name = getattr(llm_with_tools, 'model_name', 'Attribute not found')
        actual_api_key = getattr(llm_with_tools, 'openai_api_key', 'Attribute not found')
        api_key_snippet = f"{actual_api_key[:5]}...{actual_api_key[-4:]}" if isinstance(actual_api_key, str) and len(actual_api_key) > 9 else actual_api_key
        logger.debug(f"Invoking LLM. Bound Model Name: {actual_model_name}, API Key Used (snippet): {api_key_snippet}")
        # --- END ADDED DEBUG LOGGING --- 

        # Invoke the LLM with the prepared messages
        logger.info("Вызываю LLM с инструментами...")
        try:
            # --- BEGIN DETAILED PROMPT LOGGING (DEBUG Level) --- 
            logger.info("--- Preparing Prompt Messages for LLM ---")
            logger.info(f"Total messages in prompt: {len(prompt_messages)}")
            for msg in prompt_messages:
                # Use type(msg).__name__ as .type is not standard on BaseMessage
                msg_type = type(msg).__name__ 
                content_repr = repr(getattr(msg, 'content', 'N/A'))[:500] # Use getattr for safety
                logger.info(f"  - Type: {msg_type}, Content Start: {content_repr}...")
            logger.info("--- End Prompt Messages ---")
            # --- END DETAILED PROMPT LOGGING --- 

            # logger.info(f"Sending {len(prompt_messages)} messages to LLM.") # Removed previous INFO log
            # logger.info(f"LLM Input Messages:\n{formatted_prompt_log}") # Removed previous DEBUG log
            response = await llm_with_tools.ainvoke(prompt_messages)
            # Log the raw response object
            logger.info(f"LLM Raw Response: {response}")
            
            # --- BEGIN ADDED DEBUG LOGGING --- 
            # Extract and log which model was ACTUALLY used by OpenAI
            if hasattr(response, 'response_metadata') and 'model_name' in response.response_metadata:
                actual_model = response.response_metadata['model_name']
                logger.warning(f"ACTUAL MODEL USED BY OPENAI: {actual_model} (may differ from requested model)")
            # --- END ADDED DEBUG LOGGING --- 
            
            # Ensure response is AIMessage and has content
            if not isinstance(response, AIMessage):
                logger.error(f"LLM response is not AIMessage: {type(response)}")
                # Handle error: maybe return a default message or raise exception
                generation_result = AIMessage(content="Ошибка: Неожиданный формат ответа от LLM.")
            elif not hasattr(response, 'content') or not response.content:
                 logger.warning(f"LLM response (AIMessage) has no content: {response}")
                 # Handle case with no content - maybe it made a tool call or refused?
                 # For now, let's provide a generic response if no tool call either
                 if not response.tool_calls:
                     generation_result = AIMessage(content="Я не смог сгенерировать ответ на ваш запрос.")
                 else:
                     generation_result = response # Pass tool calls through
            else:
                 generation_result = response

        except Exception as e:
            # This block handles errors during the API call itself
            logger.exception("Ошибка при вызове LLM или обработке ответа:")
            # Return an error message within the expected structure
            generation_result = AIMessage(content="Извините, произошла внутренняя ошибка при генерации ответа.")
            # Ensure state consistency even after API error
            updated_messages = messages + [generation_result]
            tool_calls = None # No tool calls if the API failed

        logger.info(f"LLM ответил. Результат (тип: {type(generation_result)}): {str(generation_result)[:200]}...")

        # Check for tool calls in the response message - This info is now *in* the returned AIMessage
        # if isinstance(response, AIMessage) and response.tool_calls:
        #     # ... logging ...
        # else:
        #     # ... logging ...
        # tool_calls = None # No longer needed as separate return

        # Return the AIMessage in the format expected by the checkpointer for appending
        return {"messages": [generation_result]} 

    except Exception as e:
        # This block handles errors BEFORE/DURING the API call or tool binding
        logger.error(f"Ошибка во время генерации LLM или привязки инструментов: {e}", exc_info=True)
        # Create an error message to return
        error_response_message = AIMessage(content="Извините, произошла ошибка при обработке вашего запроса.")
        # Return the error message for appending to history
        return {"messages": [error_response_message]} 