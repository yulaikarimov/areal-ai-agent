"""Factory function to create CRM adapter instances based on configuration."""

import logging
from typing import Optional

from .base import CRMWrapper
from .amocrm import AmoCRMAdapter
from src.config.settings import settings

logger = logging.getLogger(__name__)


def get_crm_adapter() -> Optional[CRMWrapper]:
    """
    Instantiates and returns a CRM adapter based on the provider specified
    in the application settings.

    Reads CRM_PROVIDER from the settings object.

    Returns:
        An instance of a class inheriting from CRMWrapper if the provider
        is supported and configured correctly, otherwise None.
    """
    provider = settings.CRM_PROVIDER.lower()
    logger.info(f"Попытка настройки адаптера CRM для провайдера: {provider}")

    if provider == "amocrm":
        try:
            # AmoCRMAdapter.__init__ logs a warning if not configured but doesn't raise
            adapter = AmoCRMAdapter()
            if not adapter.is_configured:
                logger.error(
                    "Выбран провайдер AmoCRM, но API ключ или Base URL отсутствуют "
                    "в настройках. Адаптер не будет работать."
                )
                return None # Return None explicitly if not configured
            logger.info("Адаптер AmoCRM успешно создан.")
            return adapter
        except Exception as e:
            # Catch any unexpected errors during instantiation
            logger.error(f"Не удалось создать экземпляр AmoCRMAdapter: {e}", exc_info=True)
            return None

    # --- Add elif blocks for other CRM providers here ---
    # elif provider == "hubspot":
    #     # ... import HubspotAdapter
    #     # ... check settings.HUBSPOT_API_KEY etc.
    #     # ... instantiate and return HubspotAdapter or None
    #     pass

    else:
        logger.error(f"Неподдерживаемый провайдер CRM в конфигурации: {provider}")
        return None 