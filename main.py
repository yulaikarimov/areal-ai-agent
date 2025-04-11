"""Main entry point for the AI Customer Service Agent application."""

import asyncio
import logging
import sys
import signal # For handling shutdown signals
from telegram import Update # <-- Add this import

# Import the logging setup function first to configure logging early
from src.utils.logging_config import setup_logging

# Import the function to setup the Telegram bot application
from src.integrations.messengers.telegram import setup_bot
# Import checkpointer context factory and graph compilation function
from src.memory.checkpointer import get_checkpointer_context
from src.agent.graph import compile_graph

logger = logging.getLogger(__name__) # Define logger after setup

# --- Main Application Coroutine --- 

async def main() -> None:
    """Asynchronous main function to initialize and run the Telegram bot."""
    # --- Setup Logging FIRST --- 
    setup_logging()
    # ---------------------------
    logger.info("Запуск приложения...")
    
    application = None # Initialize application variable
    checkpointer_context = get_checkpointer_context() # Get the context manager
    
    if not checkpointer_context:
        logger.critical("Не удалось получить контекст чекпоинтера. Невозможно запустить приложение.")
        return

    try:
        # Start the checkpointer context manager
        async with checkpointer_context as checkpointer:
            logger.info("Контекст чекпоинтера установлен.")

            # Compile the graph INSIDE the context manager
            graph = await compile_graph(checkpointer)
            if not graph:
                logger.critical("Компиляция графа не удалась. Невозможно запустить бота.")
                return # Exit if graph compilation fails

            # Setup the telegram application instance, passing the compiled graph
            application = await setup_bot(graph)

            # Initialize the application (connects, etc.)
            logger.info("Инициализация приложения бота...")
            await application.initialize()

            # Start polling in the background. This does NOT block.
            logger.info("Запуск обработки сообщений бота...")
            await application.start()
            await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)

            # Keep the application running until interrupted
            logger.info("Бот запущен. Нажмите Ctrl+C для остановки.")
            while True:
                await asyncio.sleep(3600) # Sleep for a long time

    except (KeyboardInterrupt, SystemExit): # Catch signals gracefully
        logger.info("Получен сигнал завершения работы.")
    except Exception as e:
         logger.critical(f"Приложение столкнулось с критической ошибкой: {e}", exc_info=True)
    finally:
        # --- Cleanup ---
        # Check if application and updater exist and are running before stopping
        if (
            application is not None # Check if application was assigned
            and application.updater 
            and application.updater.running
        ):
            logger.info("Остановка обработки сообщений...")
            await application.updater.stop()
        # Check if application itself needs stopping (separate from polling)
        if 'application' in locals() and application.running:
            logger.info("Завершение работы приложения...")
            await application.stop()
            await application.shutdown()
            logger.info("Приложение корректно завершило работу.")
        else:
             logger.info("Приложение завершилось или не смогло полностью запуститься.")

# --- Entry Point --- 

if __name__ == "__main__":
    # Standard pattern to run the main async function
    try:
        asyncio.run(main())
    except Exception as e:
        # Catch errors during asyncio.run itself (less likely now)
        logging.critical(f"Ошибка выполнения asyncio.run: {e}", exc_info=True)
        sys.exit(1)
    except KeyboardInterrupt:
         # This might be caught by the inner handler, but good to have
         logging.info("Приложение остановлено сочетанием клавиш KeyboardInterrupt (main).")
         sys.exit(0) 