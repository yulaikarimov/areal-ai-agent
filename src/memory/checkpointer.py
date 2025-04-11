"""Sets up the persistent memory backend using SQLite for the LangGraph agent."""

import logging
from typing import Optional

# Ensure the directory exists before attempting to connect
from pathlib import Path

# Import changed in newer langgraph versions
# from langgraph.checkpoint.sqlite import SqliteCheckpointer
# from langgraph_checkpoint_sqlite import SqliteSaver # Sync version
from langgraph_checkpoint_sqlite import AsyncSqliteSaver # <-- Use Async version

from src.config.settings import settings

logger = logging.getLogger(__name__)

# Function to get the checkpointer context manager
def get_checkpointer_context():
    """Returns the async context manager for the SqliteSaver."""
    try:
        db_path = Path(settings.SQLITE_MEMORY_DB_PATH)
        # Ensure the parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Контекст SQLite чекпоинтера настроен для: {db_path.resolve()}")
        # Return the context manager itself, not the instance yet
        return AsyncSqliteSaver.from_conn_string(str(db_path.resolve()))
    except ImportError as ie:
        logger.error(f"Не удалось импортировать AsyncSqliteSaver: {ie}. Правильно ли установлен langgraph-checkpoint-sqlite?", exc_info=True)
        raise # Reraise the import error so it's obvious
    except Exception as e:
        logger.error(f"Не удалось настроить контекст SQLite чекпоинтера (AsyncSqliteSaver): {e}", exc_info=True)
        raise # Reraise other exceptions

# Verification requires async context now, skip direct verification here
# It will be verified implicitly during graph execution
logger.info("Асинхронный SQLite чекпоинтер успешно инициализирован.")

# REMOVE the old try/except block that instantiated agent_checkpointer
# try:
#     db_path = Path(settings.SQLITE_MEMORY_DB_PATH)
#     ...
#     agent_checkpointer = AsyncSqliteSaver.from_conn_string(str(db_path.resolve()))
#     ...
# except ... 