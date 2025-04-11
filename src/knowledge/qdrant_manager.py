"""Manages interaction with the Qdrant vector database."""

import logging
from typing import List, Optional

from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, PointStruct, UpdateResult, Filter, CollectionStatus

from src.config.settings import settings

logger = logging.getLogger(__name__)


class QdrantManager:
    """Handles Qdrant client initialization, collection management, and operations."""

    def __init__(self) -> None:
        """
        Initializes the Qdrant client using settings and checks connection.
        """
        self.collection_name: str = settings.QDRANT_COLLECTION_NAME
        try:
            self.client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=settings.QDRANT_API_KEY,
                # prefer_grpc=True, # Optional: Consider enabling for performance
                timeout=20 # Set a reasonable timeout
            )
            # Basic health check - Rely on instantiation success
            # self.client.list_collections() # Removed, causes AttributeError
            logger.info(
                f"Успешно подключено к Qdrant на "
                f"{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
            )
        except Exception as e:
            logger.error(f"Не удалось подключиться к Qdrant: {e}", exc_info=True)
            # Depending on the application's needs, you might want to raise
            # the exception or handle it differently (e.g., disable DB features)
            raise ConnectionError(f"Не удалось подключиться к Qdrant: {e}") from e

    def ensure_collection_exists(
        self,
        vector_size: int,
        distance: models.Distance = models.Distance.COSINE
    ) -> None:
        """
        Checks if the specified collection exists, and creates it if not.

        Args:
            vector_size: The dimensionality of the vectors to be stored.
            distance: The distance metric to use for vector comparison.
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)
            if collection_info.status == CollectionStatus.GREEN:
                logger.info(
                    f"Коллекция '{self.collection_name}' уже существует."
                )
                # Optional: Verify existing config (vector_size, distance) matches
                # current_config = collection_info.vectors_config.params
                # if current_config.size != vector_size or current_config.distance != distance:
                #     logger.warning(f"Collection '{self.collection_name}' exists but config mismatch!")
            else:
                 logger.warning(
                    f"Коллекция '{self.collection_name}' существует, но статус "
                    f"{collection_info.status}. Пытаюсь продолжить."
                )

        except Exception as e:
            # Catching a broad exception as client behavior for non-existent
            # collections might vary slightly across versions. Specific exceptions
            # like `UnexpectedResponse` or `ValueError` could be caught if known.
            logger.warning(
                f"Коллекция '{self.collection_name}' не найдена или ошибка проверки: {e}. "
                f"Пытаюсь создать её."
            )
            try:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=distance),
                    # Optional: Add other configurations like HNSW parameters here
                    # hnsw_config=models.HnswConfigDiff(...),
                    # quantisation_config=models.ScalarQuantization(...)
                )
                logger.info(
                    f"Успешно создана коллекция '{self.collection_name}' "
                    f"с размером вектора {vector_size} и метрикой расстояния {distance}."
                )
            except Exception as create_error:
                logger.error(
                    f"Не удалось создать коллекцию '{self.collection_name}': {create_error}",
                    exc_info=True
                )
                raise  # Re-raise the exception after logging

    def delete_collection(self) -> bool:
        """
        Deletes the configured collection from Qdrant.

        Returns:
            bool: True if deletion was successful or collection didn't exist, False otherwise.
        """
        if not self.client:
            logger.error("Клиент Qdrant недоступен, невозможно удалить коллекцию.")
            return False
        
        logger.warning(f"Попытка удаления коллекции '{self.collection_name}'...")
        try:
            operation_result = self.client.delete_collection(collection_name=self.collection_name)
            if operation_result:
                logger.info(f"Коллекция '{self.collection_name}' успешно удалена.")
                return True
            else:
                # Handle cases where deletion might return False (e.g., already deleted)
                logger.warning(f"Коллекция '{self.collection_name}' возможно не существовала или операция удаления вернула False.")
                # Consider returning True here as the end state (no collection) is achieved
                return True 
        except Exception as e:
            # Catch potential errors like connection issues or unexpected API responses
            logger.error(f"Не удалось удалить коллекцию '{self.collection_name}': {e}", exc_info=True)
            return False

    def upsert_points(self, points: List[PointStruct]) -> Optional[UpdateResult]:
        """
        Upserts (inserts or updates) points into the collection.

        Args:
            points: A list of PointStruct objects to upsert.

        Returns:
            Optional[UpdateResult]: The result of the upsert operation, or None if failed.
        """
        if not self.client:
            logger.error("Клиент Qdrant недоступен, невозможно добавить точки.")
            return None
            
        if not points:
            logger.warning("Вызван upsert с пустым списком точек. Операция не выполнена.")
            return None
            
        logger.debug(f"Попытка добавления {len(points)} точек...")
        try:
            # Use wait=True for synchronous confirmation
            operation_info: UpdateResult = self.client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True # wait=True ensures operation is finished before returning
            )
            logger.debug(f"Результат операции upsert: {operation_info.status if operation_info else 'N/A'}")
            # Consider adding more robust status checking if needed
            # if operation_info and operation_info.status != models.UpdateStatus.COMPLETED:
            #    logger.warning(f"Upsert operation status: {operation_info.status}")
            return operation_info
        except Exception as e:
            logger.error(f"Не удалось добавить точки: {e}", exc_info=True)
            # Handle error appropriately
            return None

    def search(
        self,
        query_vector: List[float],
        query_filter: Optional[models.Filter] = None,
        limit: int = 5,
        **kwargs # Allow passing other search parameters like score_threshold
    ) -> List[models.ScoredPoint]:
        """
        Performs a vector search in the collection.

        Args:
            query_vector: The vector to search for.
            query_filter: Optional filter to apply during the search (for RBAC).
            limit: The maximum number of results to return.
            **kwargs: Additional search parameters (e.g., score_threshold).

        Returns:
            A list of ScoredPoint objects representing the search results.
        """
        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
                **kwargs
            )
            logger.debug(f"Поиск нашел {len(search_result)} результатов.")
            return search_result
        except Exception as e:
            logger.error(f"Не удалось выполнить поиск: {e}", exc_info=True)
            # Handle error appropriately, maybe raise or return empty list
            return []


# Create a singleton instance for easy import
# Note: Ensure logging is configured before this module is imported if logging
# within __init__ is critical for initial setup diagnosis.
try:
    qdrant_manager = QdrantManager()
except ConnectionError:
    # If connection fails on startup, set manager to None or handle gracefully
    qdrant_manager = None
    logger.critical("Инициализация QdrantManager не удалась из-за ошибки подключения.")
    # Depending on application design, might exit or continue in degraded mode 