"""Telegram bot integration using python-telegram-bot."""

import asyncio
import logging
from typing import Optional, Dict, Any

from langchain_core.messages import HumanMessage, AIMessage
from telegram import Update, error
from telegram.ext import (
    Application, CommandHandler, ContextTypes, MessageHandler, filters
)

# Import the compile function and the placeholder variable
# from src.agent.graph import compile_graph, agent_graph 
# We only need the placeholder now
from src.agent.graph import agent_graph 
from src.config.settings import settings

logger = logging.getLogger(__name__)

# Remove the immediate check, compilation happens in setup_bot
# _GRAPH_AVAILABLE = agent_graph is not None
# if not _GRAPH_AVAILABLE:
#     logger.critical(
#         "Telegram Bot: Agent graph is not available! Please check graph compilation."
#     )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles incoming text messages from users.

    Invokes the agent graph asynchronously for the user's input, using the
    Telegram user ID as the thread_id for persistent memory.
    Streams the response back by editing an initial placeholder message.
    """
    # Check if agent_graph was successfully compiled during setup_bot
    if agent_graph is None:
        logger.error("Граф агента недоступен (ошибка компиляции?), не могу обработать сообщение.")
        if update.message:
            await update.message.reply_text(
                "Извините, сервис в данный момент недоступен. Пожалуйста, попробуйте позже."
            )
        return

    if not update.message or not update.message.text:
        logger.debug("Ignoring non-text message update.")
        return

    user_input = update.message.text
    if not update.effective_user:
        logger.warning("Не удалось получить ID пользователя из обновления. Игнорирую сообщение.")
        return
    user_id = str(update.effective_user.id) # Use effective_user for safety
    chat_id = update.message.chat_id

    logger.info(f"Получено сообщение от пользователя {user_id} в чате {chat_id}: '{user_input[:50]}...'")

    # --- Determine User Role ---
    # TODO: Implement proper role determination logic based on user_id
    #       For example, check against a list/DB of known employee IDs.
    #       Consider loading internal IDs securely from config/env.
    known_employee_ids = {} # Placeholder - Replace with actual internal user IDs if needed
    if user_id in known_employee_ids:
        user_role = "employee" # Example internal role
    else:
        user_role = "public" # Default role for external/unknown users
    logger.info(f"Назначена роль '{user_role}' пользователю {user_id}")

    # --- Prepare Graph Input and Config ---
    # The initial state passed to the graph
    # We provide the user input. Checkpointer handles loading messages.
    graph_input = {
        "input": user_input,
        # "messages": [HumanMessage(content=user_input)], # REMOVED: Checkpointer loads history
        # Pass the determined role to the agent state
        "user_role": user_role
    }

    # Configuration for the graph invocation, specifying the thread_id
    config = {"configurable": {"thread_id": user_id}}

    # --- Send Initial Acknowledgement ---
    message_id = None # Initialize message_id
    try:
        # Send placeholder and store the message object
        sent_message = await update.message.reply_text("Печатаю...")
        message_id = sent_message.message_id # Store the ID
        logger.debug(f"Sent placeholder message with ID: {message_id} to chat {chat_id}")
    except Exception as e:
        logger.error(f"Не удалось отправить первоначальное подтверждение пользователю {user_id}: {e}")
        return # Cannot proceed if we couldn't send the initial message

    # --- Stream Graph Execution ---
    final_answer = "Произошла ошибка при обработке вашего запроса." # Initialize with default error
    try:
        logger.info(f"Запуск обработки сообщения от {user_id} через LangGraph...")

        # --- Use ainvoke to get the final state directly --- 
        logger.info("Вызов agent_graph.ainvoke для получения конечного состояния...")
        final_state = await agent_graph.ainvoke(graph_input, config=config)
        logger.debug(f"Получено конечное состояние от ainvoke: {final_state}")

        # --- Extract Final Answer from the Final State --- 
        if final_state and isinstance(final_state, dict) and "generation" in final_state:
            generation_output = final_state["generation"]
            # Check if the generation output itself is valid
            if isinstance(generation_output, str) and generation_output:
                final_answer = generation_output
                logger.info(f"Извлечен финальный ответ из конечного состояния: {final_answer[:100]}...")
            else:
                logger.warning(f"Ключ 'generation' в конечном состоянии не является допустимой строкой: {type(generation_output)}")
        else:
            logger.warning("Конечное состояние не содержит допустимого ключа 'generation'.")
            
        # --- Remove the old astream loop and its logic --- 
        # The old astream logic is now removed as ainvoke is used.
        
        # Edit the original message with the final response
        if message_id:
            logger.info(f"Редактирование сообщения {message_id} с финальным ответом для пользователя {user_id}: {final_answer[:100]}...")
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=final_answer
            )
        else: # Should not happen if initial message was sent, but good practice
             logger.warning("Не удалось отредактировать сообщение, так как message_id не найден. Отправка нового сообщения.")
             await update.message.reply_text(final_answer)

    except Exception as e:
        # Log the specific exception type and message
        logger.error(f"Ошибка вызова графа агента для пользователя {user_id}: {type(e).__name__} - {e}", exc_info=True)
        final_error_message = "Извините, произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова."
        # Attempt to update the message with a generic error
        if message_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=final_error_message
                )
            except Exception as edit_e:
                logger.error(f"Не удалось отредактировать сообщение {message_id} с сообщением об ошибке для {user_id}: {edit_e}")
        else: # Fallback if initial message failed or ID was lost
             logger.error(f"Не удалось отправить сообщение об ошибке пользователю {user_id}, так как message_id отсутствует.")
             # Optionally send a new message here if critical
             # await update.message.reply_text(final_error_message)


# setup_bot now takes the compiled graph as an argument
async def setup_bot(compiled_graph: Any) -> Application:
    """Initializes the Telegram bot application using the pre-compiled agent graph and adds handlers."""
    global agent_graph # Declare intent to modify the global variable

    if not settings.TELEGRAM_BOT_TOKEN:
        logger.critical("TELEGRAM_BOT_TOKEN не указан в настройках. Невозможно запустить бота.")
        raise ValueError("Отсутствует TELEGRAM_BOT_TOKEN")
    
    # --- Assign the Compiled Graph --- 
    if compiled_graph is None:
         logger.critical("Предоставленный compiled_graph равен None. Невозможно настроить Telegram бота.")
         raise RuntimeError("Граф агента недоступен.")
    else:
        # Assign the pre-compiled graph to the module-level variable
        agent_graph = compiled_graph 
        logger.info("Используется предоставленный скомпилированный граф агента.")

    # --- Initialize Bot --- 
    logger.info("Инициализация Telegram приложения...")
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # --- Add Handlers --- 
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    application.add_handler(message_handler)

    # Optional: Add CommandHandlers later
    # start_handler = CommandHandler('start', start_command_callback)
    # application.add_handler(start_handler)
    # help_handler = CommandHandler('help', help_command_callback)
    # application.add_handler(help_handler)

    logger.info("Telegram приложение инициализировано с обработчиками.")
    return application 