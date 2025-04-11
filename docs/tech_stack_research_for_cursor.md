--- START OF FILE tech_stack_research_for_cursor.md ---

# Tech Stack Research & Implementation Directives for Cursor AI: AI Customer Service Agent (v3.1)

**Purpose for Cursor AI:** This document details the chosen technologies, specific library versions, implementation patterns, and best practices for building the AI Customer Service Agent. Use this as the primary technical reference guide. It complements `project_concept_for_cursor.md`.

**Core Directive:** Implement the project following the recommendations and code patterns outlined below to ensure consistency, maintainability, security, and alignment with project goals (flexibility, RBAC, persistence, automated ingestion).

## 1. Final Technology Stack & Recommended Versions

**Directive:** Use the following libraries and versions unless strong justification exists otherwise. Verify latest *compatible* minor/patch versions before finalizing `requirements.txt`.

| Library                 | Recommended Version(s) | Key Directive / Note                                                                                             |
| :---------------------- | :--------------------- | :--------------------------------------------------------------------------------------------------------------- |
| **Python**              | 3.10 - 3.12            | Use a consistent version across development and deployment.                                                       |
| **LangChain (core)**    | ~0.3.x                 | Use latest stable 0.3.x branch. Check integration package versions.                                              |
| **LangGraph**           | ~0.3.x                 | Use version compatible with LangChain core.                                                                       |
| **Qdrant Client (Py)**  | ~1.13.x                | **CRITICAL:** Match major version with Qdrant Server.                                                              |
| **Qdrant Server**       | Match Client           | Run via Docker locally initially. Plan for cloud/dedicated server if load increases.                                |
| **OpenAI (Python)**     | ~1.70.x                | Primary LLM/Embedding provider.                                                                                  |
| **Anthropic (Python)**  | ~0.49.x                | Secondary provider option (ensure factory pattern supports it).                                                  |
| **python-telegram-bot** | ~22.x                  | **Preferred** Telegram library due to docs/community. Fully async.                                                 |
| **aiogram**             | ~3.19.x                | Alternative Telegram library.                                                                                    |
| **Requests**            | ~2.32.x                | For generic REST API calls (CRM).                                                                                |
| **Pydantic**            | ~2.11.x                | Core for LangGraph state and tool schemas. Be mindful of v1/v2 compatibility (`pydantic-compat` if needed).      |
| **Unstructured**        | ~0.17.x                | **Primary tool** for automated document loading (`UnstructuredLoader`).                                            |
| **SQLite3**             | Built-in               | **Mandatory** backend for LangGraph Checkpointer (persistent memory) and feedback storage.                       |
| **python-dotenv**       | Latest                 | For managing environment variables locally (`.env` file).                                                          |

## 2. Implementation Directives & Best Practices

**(Referencing sections from the original Consolidated Report v3.1)**

### 3.2 Automated & Intelligent Document Ingestion
*   **Directive:** Use `langchain_unstructured.UnstructuredLoader` as the default loader.
*   **Directive:** Enhance ingestion by automatically generating metadata (summaries, keywords) using a cost-effective LLM (e.g., GPT-3.5-Turbo) via `LLMChain`. Store this metadata in Qdrant payload.
*   **Directive:** Extract structural metadata (headers, sections) using Unstructured.
*   **Directive:** **CRITICAL:** Embed RBAC metadata (`allowed_roles` list) into *every* chunk's payload in Qdrant.
*   **Consider:** Using semantic chunking or reranking if basic RAG proves insufficient.
*   **Implement:** Robust error handling and basic quality checks (spot checks, RAG evaluation dataset).

### 3.3 LangChain & LangGraph
*   **Directive:** Define a clear `AgentState` (TypedDict or Pydantic).
*   **Directive:** Structure the graph with nodes for `retrieve`, `generate`, `tools`, `route`.
*   **Directive:** **CRITICAL:** Use `langgraph.checkpoint.sqlite.SqliteCheckpointer` for persistent memory. Configure it using the messenger `user_id` as `thread_id`. See code example in original report (Section 3.3).
*   **Directive:** Implement the Qdrant retrieval node *with* RBAC filtering based on user role (passed in state/config).
*   **Directive:** Define tools using `@tool` decorator, clear docstrings, Pydantic schemas for args, and robust `try-except` blocks. See CRM tool example in original report (Section 3.4).
*   **Directive:** Handle "no documents found" scenarios gracefully in the graph flow.

### 3.4 Qdrant (Vector DB)
*   **Directive:** Run via Docker locally (`qdrant/qdrant`) with volume mapping for persistence.
*   **Directive:** Create collection with `COSINE` distance and vector size matching the chosen embedding model (e.g., 1536 for `text-embedding-3-small`).
*   **Directive:** **CRITICAL:** Implement RBAC filtering during search using `models.Filter` based on `allowed_roles` metadata. See code example in original report (Section 3.4).
*   **Implement:** Document update/deletion logic using `document_id` filtering (delete-then-upsert pattern). See code example in original report (Section 3.4).

### 3.5 LLM & Embeddings
*   **Directive:** **CRITICAL:** Implement a factory pattern (like the example in original report, Section 3.5) to allow easy switching of LLM providers (OpenAI, Anthropic) and models via environment variables/config.
*   **Directive:** Use `ChatPromptTemplate` for structured prompts including history, query, and *formatted* retrieved context.
*   **Implement:** Context window management (truncation strategies for history/context).
*   **Implement:** API call retries (using LangChain client settings or `tenacity`).

### 3.6 Messenger Integration
*   **Directive:** Use `python-telegram-bot`. Implement async handlers.
*   **Directive:** **CRITICAL:** Map Telegram `user_id` / WhatsApp phone number consistently to the LangGraph `thread_id` for memory persistence.
*   **Implement:** Logic to extract user message, call the compiled graph with user-specific config (`thread_id`), and send back the final response. See basic handler example in original report (Section 3.6).

### 3.7 CRM Integration
*   **Directive:** **CRITICAL:** Implement the CRM **Abstraction Layer** (e.g., `CRMWrapper` ABC and `AmoCRMAdapter` concrete class). See code example in original report (Section 3.7).
*   **Directive:** Use a factory (`get_crm_adapter`) to instantiate the correct adapter based on config.
*   **Directive:** Implement the initial `AmoCRMAdapter` using `requests` to call its v4 REST API. Handle authentication via Bearer token securely.
*   **Directive:** Wrap adapter methods as LangChain `@tool`s with clear descriptions and input schemas. **CRITICAL:** Process the raw CRM response (dict) into a user-friendly string summary within the tool before returning.

### 3.8 Deployment, Persistence & Observability
*   **Directive:** Use **SQLite** via Python's `sqlite3` module for storing feedback data. See example `init_feedback_db` and `save_feedback` functions in original report (Section 3.8).
*   **Directive:** Use **Docker** and **Docker Compose** for containerization and local orchestration (App + Qdrant).
*   **Implement:** Structured logging using Python's `logging` module (JSON format recommended).
*   **Strongly Recommended:** Integrate **LangSmith** for tracing and debugging. Set `LANGCHAIN_TRACING_V2=true` and other relevant environment variables.

### 3.9 Feedback Loop & Agent Improvement
*   **Implement:** Simple feedback collection in the messenger (buttons or `/feedback` command).
*   **Implement:** Store feedback using the `save_feedback` function into the SQLite database.
*   **Process:** Establish a *manual* review process for analyzing feedback and updating KB docs or prompts accordingly.

### 3.10 Security Considerations
*   **CRITICAL:** **Never** commit secrets. Use environment variables (`python-dotenv` locally) and a secrets manager in production.
*   **CRITICAL:** Implement Qdrant RBAC filtering diligently on *all* retrievals.
*   **CRITICAL:** Validate and sanitize tool inputs/outputs. Do not execute arbitrary code suggested by the LLM.
*   **Implement:** Rate limiting at the messenger bot level.
*   **Review:** Generated code for common vulnerabilities (OWASP Top 10 relevant aspects).
*   **Minimize:** PII logging.

## 4. General Cursor AI Usage Notes (from Best Practices Guide)

*   Use `@file` (`project_concept_for_cursor.md`, `tech_stack_research_for_cursor.md`) extensively to provide context.
*   Use `@Codebase` once the project structure exists.
*   Break down complex feature requests into smaller prompts.
*   Use "Ask any questions for clarity" at the end of prompts.
*   Leverage Edit mode (Cmd/Ctrl+K) for refinements.
*   Use `@git` for context on changes and generating commit messages.
*   Use Notepads for common prompts/tasks.

--- END OF FILE tech_stack_research_for_cursor.md ---