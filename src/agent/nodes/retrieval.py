"""Node for retrieving relevant documents from the Qdrant knowledge base."""

import logging
from typing import Dict, List, Optional

from qdrant_client import models

from src.agent.state import AgentState
from src.config.embedding_factory import get_embedding_model
from src.knowledge.qdrant_manager import qdrant_manager

logger = logging.getLogger(__name__)

# --- Module Level Initialization --- 

# Check Qdrant availability
QDRANT_AVAILABLE = qdrant_manager is not None
if not QDRANT_AVAILABLE:
    logger.warning(
        "Менеджер Qdrant не инициализирован. Узел извлечения будет нефункциональным."
    )

# Initialize embedding model
_embedding_model = None
_EMBEDDING_AVAILABLE = False
if QDRANT_AVAILABLE: # Only try to get embedder if Qdrant is available
    try:
        _embedding_model = get_embedding_model()
        _EMBEDDING_AVAILABLE = _embedding_model is not None
        if not _EMBEDDING_AVAILABLE:
             logger.warning(
                "Модель эмбеддингов не инициализирована. Узел извлечения будет нефункциональным."
            )
    except ValueError as e:
        logger.error(f"Не удалось инициализировать модель эмбеддингов: {e}", exc_info=True)
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"Непредвиденная ошибка при инициализации модели эмбеддингов: {e}", exc_info=True)


def retrieve_documents(state: AgentState) -> Dict[str, Optional[List[str]]]:
    """
    Retrieves documents relevant to the user's input from Qdrant.

    Embeds the user input, constructs an RBAC filter based on the user role,
    performs a search in Qdrant, and formats the results.

    Args:
        state: The current state of the agent graph.

    Returns:
        A dictionary containing the update for the 'retrieved_docs' key in the state.
        Value is a list of formatted document strings or None if retrieval fails.
    """
    logger.info("---NODE: retriever---")
    retrieved_docs_list: Optional[List[str]] = None

    # Check prerequisites
    if not QDRANT_AVAILABLE or not _EMBEDDING_AVAILABLE or qdrant_manager is None or _embedding_model is None:
        logger.warning("Необходимые компоненты поиска недоступны (Qdrant или модель эмбеддингов). Пропускаю поиск.")
        return {"retrieved_docs": None} # Indicate failure explicitly

    user_input = state['input']
    user_role = state.get('user_role') # Use .get for safer access

    if not user_input:
        logger.warning("В состоянии не найден пользовательский ввод. Невозможно извлечь документы.")
        return {"retrieved_docs": None}

    logger.debug(f"Ищу документы для запроса: '{user_input[:100]}...' с ролью пользователя: {user_role}")

    try:
        # 1. Generate Query Embedding
        query_embedding = _embedding_model.embed_query(user_input)

        # 2. Construct RBAC Filter
        query_filter: Optional[models.Filter] = None
        if user_role:
            logger.debug(f"Применяю RBAC фильтр для роли: {user_role}")
            # Assumes 'allowed_roles' is a list of strings in Qdrant metadata
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="allowed_roles", # CORRECT KEY: Refer directly to the payload field
                        match=models.MatchAny(any=[user_role])
                    )
                ]
            )
        else:
            logger.warning("Роль пользователя не указана в состоянии. Выполняю поиск без RBAC фильтрации.")

        # 3. Search Qdrant
        search_results = qdrant_manager.search(
            query_vector=query_embedding,
            query_filter=query_filter,
            limit=5 # Configurable limit
        )

        # 4. Process Results
        if search_results:
            retrieved_docs_list = []
            scores = [] # List to hold scores for logging
            for hit in search_results:
                scores.append(hit.score) # Log the score
                # Ensure payload and text exist
                payload = hit.payload if hit.payload else {}
                content = payload.get('text', '[Содержимое недоступно]')
                source = payload.get('source', 'Н/Д')
                # Simple formatting, can be customized
                formatted_doc = f"Источник: {source}\nСодержимое: {content}"
                retrieved_docs_list.append(formatted_doc)
            logger.info(f"Найдено {len(retrieved_docs_list)} документов (без порога). Scores: {scores}")
        else:
            logger.info("Не найдено документов, соответствующих запросу и фильтрам (порог отключен).")
            retrieved_docs_list = [] # Return empty list if no results

    except Exception as e:
        logger.error(f"Ошибка при поиске документов: {e}", exc_info=True)
        retrieved_docs_list = None # Indicate failure explicitly

    # Return the update for the state
    return {"retrieved_docs": retrieved_docs_list} 