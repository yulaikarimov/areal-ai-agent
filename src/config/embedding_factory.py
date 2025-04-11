"""Factory function to create embedding model instances based on configuration."""

import logging

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
# Placeholder for HuggingFace - uncomment and install `langchain-community` if needed
# from langchain_community.embeddings import HuggingFaceEmbeddings

from src.config.settings import settings

logger = logging.getLogger(__name__)


def get_embedding_model() -> Embeddings:
    """
    Instantiates and returns a LangChain embedding model based on the provider
    specified in the application settings.

    Reads EMBEDDING_PROVIDER, API keys, and model names from the settings object.

    Returns:
        An instance of a class inheriting from Embeddings.

    Raises:
        ValueError: If the configured provider is unsupported, if the required
                    API key/model name for the provider is missing, or if the
                    HuggingFace provider is selected without the necessary library.
    """
    provider = settings.EMBEDDING_PROVIDER.lower()
    logger.info(f"Attempting to configure embedding model for provider: {provider}")

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            logger.error("OpenAI API key (OPENAI_API_KEY) is missing for embeddings.")
            raise ValueError("Missing OpenAI API key in settings for embeddings.")
        if not settings.OPENAI_EMBEDDING_MODEL_NAME:
            logger.error("OpenAI embedding model name (OPENAI_EMBEDDING_MODEL_NAME) is missing.")
            raise ValueError("Missing OpenAI embedding model name in settings.")

        logger.info(f"Using OpenAI embedding model: {settings.OPENAI_EMBEDDING_MODEL_NAME}")
        return OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL_NAME,
            api_key=settings.OPENAI_API_KEY,
            # Add other parameters like dimensions if needed/supported
        )

    # elif provider == "huggingface":
    #     if not settings.HUGGINGFACE_EMBEDDING_MODEL_NAME:
    #         logger.error("HuggingFace embedding model name (HUGGINGFACE_EMBEDDING_MODEL_NAME) is missing.")
    #         raise ValueError("Missing HuggingFace embedding model name in settings.")
    #     try:
    #         from langchain_community.embeddings import HuggingFaceEmbeddings
    #         logger.info(f"Using HuggingFace embedding model: {settings.HUGGINGFACE_EMBEDDING_MODEL_NAME}")
    #         # You might need to configure device mapping (e.g., 'cpu', 'cuda')
    #         # model_kwargs = {'device': 'cpu'}
    #         # encode_kwargs = {'normalize_embeddings': False}
    #         return HuggingFaceEmbeddings(
    #             model_name=settings.HUGGINGFACE_EMBEDDING_MODEL_NAME,
    #             # model_kwargs=model_kwargs,
    #             # encode_kwargs=encode_kwargs
    #         )
    #     except ImportError:
    #         logger.error(
    #             "HuggingFace provider selected, but `langchain-community` is not installed. "
    #             "Please install it: pip install langchain-community"
    #         )
    #         raise ValueError("Missing langchain-community for HuggingFace embeddings.")

    else:
        logger.error(f"Unsupported embedding provider configured: {provider}")
        raise ValueError(f"Unsupported embedding provider: {provider}") 