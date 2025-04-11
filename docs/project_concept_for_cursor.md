--- START OF FILE project_concept_for_cursor.md (v3 - AREAL Specific) ---

# Project Concept for Cursor AI: AI Customer Service Agent for OOO NPP "AREAL"

**Purpose for Cursor AI:** This document outlines the core concept, objectives, features, and high-level architectural principles for the AI Customer Service Agent specifically tailored for **OOO NPP "AREAL"**, an environmental company specializing in hazardous waste management. Use this as the primary reference for understanding *what* needs to be built and *why*. Refer to `tech_stack_research_for_cursor.md` for technical implementation details.

## 1. Objective

Develop an AI-powered agent (manager) for **OOO NPP "AREAL"** capable of interacting with **customers (primarily legal entities/entrepreneurs) AND internal employees** via messaging platforms (Telegram, WhatsApp).
The agent must:
*   Understand user requests related to waste management, environmental services, and company operations in natural language (Russian).
*   Provide accurate information based on company documentation (licenses, service descriptions, patents, regulations) retrieved via RAG.
*   Assist users in initiating service requests (e.g., waste collection, consulting) by gathering necessary information.
*   Integrate with the company's CRM system (initially AmoCRM, requiring flexibility).
*   Reflect the company's image as a scientifically-driven, innovative, and environmentally responsible leader in hazardous waste management.

## 2. Core Features (AREAL Specific Functionality)

*   **Conversational Interface:** Natural language interaction (primarily Russian) on Telegram & WhatsApp. Maintain a professional, competent, and helpful tone aligned with "AREAL".
*   **Knowledge Base Q&A (RAG):**
    *   Answer questions about "AREAL"'s services: **waste collection, transportation, treatment, neutralization, and disposal of I-IV hazard classes** [4, 7], including specific types like **mercury-containing waste** [14], **medical/biological waste**, **oil sludge**, etc.
    *   Provide information on the company's **capabilities**: own industrial site in Ufa [12], specialized transport [20], unique technologies (pyrolysis [16], demercurization [14], water treatment [22-25, 34-39], etc.), extensive **patent portfolio (100+ for waste, 50+ for water)** [8, 22].
    *   Explain company **advantages**: full processing cycle [7], **no landfill disposal** [19], compliance with standards (GOST R, SanPiN) [13], experienced staff (PhDs, Candidates) [9].
    *   Answer questions based on **uploaded company documents** (licenses [7], certificates, service descriptions, technical regulations [60-67], etc.).
    *   **Constraint:** If information is not found in the knowledge base, state this clearly and suggest contacting a specialist (8 800 555 90 57 / office@arealnpp.ru). **Do NOT invent answers.**
*   **Request/Lead Processing:**
    *   Identify user intent to order services (waste removal, consulting, document development, tank cleaning, etc.).
    *   Guide the user to provide necessary preliminary information: **Company Name, Contact Person, Phone/Email, Waste Type/Service Needed, Volume/Quantity, Object Address.**
    *   **Constraint:** Use the `create_crm_lead` tool (once implemented) to pass this information to CRM.
    *   **Constraint:** Inform the user that the request is registered and a manager will contact them for details and pricing. **Do NOT provide quotes or confirm schedules.**
*   **CRM Integration:** Create/update records (leads, contacts) in AmoCRM (initially) via an **abstraction layer**. Use the `get_crm_customer_info` tool to fetch data for internal users/authorized requests.
*   **Semantic Memory:** Use **Qdrant** for efficient semantic search over "AREAL"'s knowledge base.
*   **Long-Term Contextual Awareness:** Maintain persistent conversation history per user via **SQLite checkpointer**.
*   **Role-Based Access Control (RBAC):** Ensure internal employees (sales, logistics, ecologists, management) access only information relevant to their role via **Qdrant metadata filtering**. Public users access only public information.
*   **Feedback Loop:** Allow employees to provide feedback on agent responses via a simple mechanism (results stored in SQLite).

## 3. Key Technologies (High-Level Overview)

*(No changes here, stack remains the same. Refer to `tech_stack_research_for_cursor.md`)*

*   Language: Python (3.10+)
*   Core AI Framework: LangChain
*   Agent Orchestration: LangGraph
*   Vector DB: Qdrant
*   LLM: Configurable (Default: GPT-4 / GPT-3.5-Turbo)
*   Embeddings: Configurable (Default: OpenAI `text-embedding-3-small`)
*   Messaging: `python-telegram-bot` / WhatsApp Business API
*   CRM: Abstraction Layer + AmoCRM Adapter
*   Persistence: SQLite
*   Document Processing: `UnstructuredLoader`

## 4. Architectural Principles & Directives (AREAL Context)

*   **RAG Pipeline:** Retrieve relevant sections from "AREAL" documents (licenses, tech descriptions, service lists) in Qdrant to augment LLM generation.
*   **LangGraph State Machine:** Model the flow: greeting -> understand request -> RAG/Tool Use -> format response -> potentially collect lead info -> final response/handoff.
*   **Tool-Based Actions:** Encapsulate CRM calls (`get_customer_info`, `create_lead`) as clearly described LangChain `Tools` reflecting "AREAL" context.
*   **CRM Abstraction:** **Mandatory.** Design for potential future CRM migration.
*   **Configurable Models:** **Mandatory.**
*   **Persistent User Memory:** **Mandatory** (SQLite Checkpointer).
*   **RBAC via Metadata:** **Mandatory.** Filter Qdrant queries based on user role (e.g., "public", "employee", "hr", "management") matched against `allowed_roles` metadata in Qdrant points.
*   **Automated Ingestion:** Use `DocumentProcessor` to automatically assign `allowed_roles` based on source directory (e.g., `data/docs_to_ingest/public/`, `data/docs_to_ingest/employee/`) or defaults when loading documents into Qdrant.
*   **Modular Design:** Maintain separation.

## 5. Integrations

*   Input/Output: Telegram, WhatsApp (Primarily Russian language).
*   Knowledge Source: Internal "AREAL" documents (presentation, licenses, service descriptions, technical specs, potentially website content).
*   Action Target: CRM System (AmoCRM initially).
*   State Storage: Qdrant (vectors+payload), SQLite (conversation state, feedback).

## 6. Development Context & Load

*   Goal: Rapid development of a reliable, maintainable agent for "AREAL".
*   Load: Low initial load.
*   Key Non-functional Requirements: Long-term memory, **Strict RBAC**, CRM/LLM flexibility, **Accuracy based on company knowledge**, **Professional Tone**.

--- END OF FILE project_concept_for_cursor.md (v3 - AREAL Specific) ---