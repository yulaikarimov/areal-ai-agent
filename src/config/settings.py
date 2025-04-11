"""Loads application settings from environment variables and .env file."""

import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.

    Attributes:
        LLM_PROVIDER: The primary LLM provider ("openai" or "anthropic").
        OPENAI_API_KEY: API key for OpenAI services.
        OPENAI_MODEL_NAME: Specific OpenAI model to use.
        ANTHROPIC_API_KEY: Optional API key for Anthropic services.
        ANTHROPIC_MODEL_NAME: Optional specific Anthropic model to use.
        EMBEDDING_PROVIDER: The provider for text embeddings ("openai" or "huggingface").
        OPENAI_EMBEDDING_MODEL_NAME: Specific OpenAI embedding model.
        HUGGINGFACE_EMBEDDING_MODEL_NAME: Optional specific HuggingFace embedding model.
        QDRANT_HOST: Hostname for the Qdrant vector database.
        QDRANT_PORT: Port number for the Qdrant vector database.
        QDRANT_API_KEY: Optional API key for Qdrant Cloud.
        QDRANT_COLLECTION_NAME: Name of the collection within Qdrant.
        TELEGRAM_BOT_TOKEN: Authentication token for the Telegram bot.
        WHATSAPP_TOKEN: Optional token for WhatsApp Business API.
        WHATSAPP_PHONE_NUMBER_ID: Optional WhatsApp phone number ID.
        WHATSAPP_VERIFY_TOKEN: Optional token for WhatsApp webhook verification.
        CRM_PROVIDER: The CRM provider being used (e.g., "amocrm").
        AMO_CRM_API_KEY: API key or token for the AmoCRM integration.
        AMO_CRM_BASE_URL: Base URL for the AmoCRM API.
        SQLITE_MEMORY_DB_PATH: Filesystem path for the agent memory SQLite DB.
        SQLITE_FEEDBACK_DB_PATH: Filesystem path for the user feedback SQLite DB.
        LANGCHAIN_TRACING_V2: Enable LangSmith tracing (True/False).
        LANGCHAIN_ENDPOINT: Endpoint URL for LangSmith.
        LANGCHAIN_API_KEY: Optional API key for LangSmith.
        LANGCHAIN_PROJECT: Optional project name for LangSmith.
        LOG_LEVEL: Logging level for the application (e.g., "INFO", "DEBUG").
    """
    # --- LLM Configuration ---
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str
    OPENAI_MODEL_NAME: str = "o3-mini"
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL_NAME: Optional[str] = "claude-3-5-sonnet-20240620"

    # --- Embedding Model Configuration ---
    EMBEDDING_PROVIDER: str = "openai"
    OPENAI_EMBEDDING_MODEL_NAME: Optional[str] = "text-embedding-3-small"
    HUGGINGFACE_EMBEDDING_MODEL_NAME: Optional[str] = None

    # --- Vector Database (Qdrant) ---
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "knowledge_base"

    # --- Messengers ---
    TELEGRAM_BOT_TOKEN: str
    WHATSAPP_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: Optional[str] = None

    # --- CRM Configuration ---
    CRM_PROVIDER: str = "amocrm"
    AMO_CRM_API_KEY: str
    AMO_CRM_BASE_URL: str

    # --- Persistence ---
    SQLITE_MEMORY_DB_PATH: str = "data/persistent/agent_memory.sqlite"
    SQLITE_FEEDBACK_DB_PATH: str = "data/persistent/feedback.sqlite"

    # --- LangSmith (Optional but Recommended) ---
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_ENDPOINT: Optional[str] = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: Optional[str] = "AI_Customer_Service_Agent"

    # --- Application Settings ---
    LOG_LEVEL: str = "DEBUG"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), '..', '..', '.env'), # Construct path to root .env
        env_file_encoding='utf-8',
        extra='ignore' # Ignore extra fields from .env
    )

# Create a single instance of the settings to be imported by other modules
settings = Settings()

# Optional: Add a simple check to ensure critical secrets are loaded
# if not settings.OPENAI_API_KEY:
#     raise ValueError("OPENAI_API_KEY must be set in the environment or .env file")
# if not settings.TELEGRAM_BOT_TOKEN:
#     raise ValueError("TELEGRAM_BOT_TOKEN must be set in the environment or .env file")
# if settings.CRM_PROVIDER.lower() == "amocrm" and (not settings.AMO_CRM_API_KEY or not settings.AMO_CRM_BASE_URL):
#     raise ValueError("AMO_CRM_API_KEY and AMO_CRM_BASE_URL must be set for the amocrm provider") 