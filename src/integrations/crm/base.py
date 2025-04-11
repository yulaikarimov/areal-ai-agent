"""Defines the abstract base class for CRM integration wrappers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class CRMWrapper(ABC):
    """
    Abstract Base Class for CRM system integrations.

    Defines a common interface for interacting with different CRM systems,
    allowing the application to switch between providers easily.
    Concrete implementations should handle provider-specific API calls,
    authentication, and error handling.
    """

    @abstractmethod
    def get_customer_info(self, customer_id: str) -> Optional[Dict[str, Any]] | str:
        """
        Fetches customer/contact information by their CRM ID.

        Args:
            customer_id: The unique identifier of the customer/contact in the CRM.

        Returns:
            A dictionary containing customer data if found and accessible,
            an error string describing the issue if the request fails or the
            customer is not found, or None if the CRM adapter is not configured.
        """
        pass

    # --- Placeholder for other common CRM operations ---

    # @abstractmethod
    # def create_lead(self, lead_data: Dict[str, Any]) -> Optional[Dict[str, Any]] | str:
    #     """
    #     Creates a new lead in the CRM.
    #
    #     Args:
    #         lead_data: A dictionary containing the lead details (e.g., name, phone,
    #                    email, custom fields).
    #
    #     Returns:
    #         A dictionary containing the newly created lead's data (e.g., ID),
    #         an error string describing the issue if creation fails, or None if the
    #         CRM adapter is not configured.
    #     """
    #     pass

    # @abstractmethod
    # def update_contact(self, contact_id: str, update_data: Dict[str, Any]) -> bool | str:
    #     """
    #     Updates an existing contact in the CRM.
    #
    #     Args:
    #         contact_id: The ID of the contact to update.
    #         update_data: A dictionary containing the fields to update.
    #
    #     Returns:
    #         True if the update was successful, an error string otherwise, or None
    #         if the CRM adapter is not configured.
    #     """
    #     pass 