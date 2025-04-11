"""Configures the application's logging setup."""

import logging
import sys

from src.config.settings import settings


def setup_logging() -> None:
    """
    Sets up the root logger with a configured level and console handler.

    Retrieves the log level from the application settings, creates a
    StreamHandler to output logs to stderr, defines a standard log format,
    and adds the handler to the root logger. It prevents adding duplicate
    handlers if called multiple times.
    """
    log_level_name = settings.LOG_LEVEL.upper()
    numeric_level = getattr(logging, log_level_name, None)

    if not isinstance(numeric_level, int):
        # Default to INFO if the level name is invalid
        logging.warning(
            f"Invalid log level '{settings.LOG_LEVEL}' in settings. "
            f"Defaulting to INFO."
        )
        numeric_level = logging.INFO

    # Get the root logger
    root_logger = logging.getLogger()

    # Prevent adding duplicate handlers
    if root_logger.hasHandlers():
        # Optional: Log a message indicating setup was already done
        # logging.debug("Logging already configured.")
        return

    root_logger.setLevel(numeric_level)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(numeric_level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    # Add formatter to handler
    console_handler.setFormatter(formatter)

    # Add handler to the root logger
    root_logger.addHandler(console_handler)

    # Optional: Log a confirmation message after setup
    # logging.info(f"Logging configured with level: {log_level_name}") 