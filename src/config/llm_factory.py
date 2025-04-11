"""Factory function to create chat model instances based on configuration."""

import logging

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from src.config.settings import settings

logger = logging.getLogger(__name__)


def get_chat_model() -> BaseChatModel:
    """
    Instantiates and returns a LangChain chat model based on the provider
    specified in the application settings.

    Reads LLM_PROVIDER, API keys, and model names from the settings object.

    Returns:
        An instance of a class inheriting from BaseChatModel.

    Raises:
        ValueError: If the configured provider is unsupported or if the
                    required API key for the provider is missing.
    """
    provider = settings.LLM_PROVIDER.lower()
    logger.info(f"Attempting to configure chat model for provider: {provider}")

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            logger.error("OpenAI API key (OPENAI_API_KEY) is missing.")
            raise ValueError("Missing OpenAI API key in settings.")

        logger.info(f"Using OpenAI model: {settings.OPENAI_MODEL_NAME}")
        return ChatOpenAI(
            model=settings.OPENAI_MODEL_NAME,
            api_key=settings.OPENAI_API_KEY
            # temperature=0 # Removed for compatibility with older models
            # Add other parameters like max_tokens if needed
        )

    elif provider == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            logger.error("Anthropic API key (ANTHROPIC_API_KEY) is missing.")
            raise ValueError("Missing Anthropic API key in settings.")

        logger.info(f"Using Anthropic model: {settings.ANTHROPIC_MODEL_NAME}")
        return ChatAnthropic(
            model=settings.ANTHROPIC_MODEL_NAME,
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=0 # Default to deterministic output
            # Add other parameters if needed
        )

    else:
        logger.error(f"Unsupported LLM provider configured: {provider}")
        raise ValueError(f"Unsupported LLM provider: {provider}") 