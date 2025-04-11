--- START OF FILE project_structure.md ---

# Project Structure Definition for Cursor AI: AI Customer Service Agent

**Purpose for Cursor AI:** This document defines the target directory and file structure for the AI Customer Service Agent project. Use this as a blueprint when creating new files or referencing existing modules. Adhering to this structure ensures consistency and helps manage complexity.

## Root Directory

```text
.
├── .env                  # Environment variables (API keys, configs) - DO NOT COMMIT
├── .gitignore            # Specifies intentionally untracked files that Git should ignore
├── README.md             # Project overview, setup instructions
├── requirements.txt      # Python package dependencies
├── Dockerfile            # Instructions to build the application Docker image
├── docker-compose.yml    # Defines services for local development (App, Qdrant)
├── main.py               # Main entry point for the application (e.g., starting the bot)
│
├── data/                 # Data storage (databases, documents)
│   ├── docs_to_ingest/   # Source documents for the knowledge base (PDF, DOCX, etc.) - Gitignore if sensitive
│   └── persistent/       # Persistent data like SQLite DBs - MUST BE GITIGNORED
│       ├── agent_memory.sqlite # DB for LangGraph persistent memory
│       └── feedback.sqlite     # DB for storing user feedback
│
├── docs/                 # Project documentation
│   ├── project_concept_for_cursor.md  # High-level project goals and features
│   ├── tech_stack_research_for_cursor.md # Technical decisions and directives
│   └── project_structure.md         # This file
│   └── adr/                           # (Optional) Architecture Decision Records
│
├── scripts/              # Utility scripts
│   └── load_knowledge_base.py # Script to process docs from data/docs_to_ingest into Qdrant
│
├── src/                  # Main source code directory
│   ├── __init__.py
│   │
│   ├── agent/            # Core LangGraph agent logic
│   │   ├── __init__.py
│   │   ├── graph.py      # Defines the LangGraph StateGraph, nodes connections
│   │   ├── state.py      # Defines the AgentState model (TypedDict or Pydantic)
│   │   └── nodes/        # Individual node functions for the graph
│   │       ├── __init__.py
│   │       ├── retrieval.py  # Node for querying Qdrant (incl. RBAC)
│   │       ├── generation.py # Node for calling LLM to generate responses
│   │       ├── routing.py    # Node for conditional logic/routing within the graph
│   │       └── tool_execution.py # Node for executing chosen tools
│   │
│   ├── config/           # Configuration loading and factories
│   │   ├── __init__.py
│   │   ├── settings.py   # Loads settings from .env, defines config models
│   │   ├── llm_factory.py # Factory function get_chat_model() for swappable LLMs
│   │   └── embedding_factory.py # Factory for swappable embedding models
│   │
│   ├── integrations/     # Modules for integrating with external services
│   │   ├── __init__.py
│   │   ├── crm/          # CRM Integration logic
│   │   │   ├── __init__.py
│   │   │   ├── base.py     # Defines the abstract CRMWrapper
│   │   │   ├── amocrm.py   # Concrete implementation for AmoCRMAdapter
│   │   │   └── factory.py  # Defines get_crm_adapter()
│   │   │
│   │   └── messengers/    # Messenger integration logic
│   │       ├── __init__.py
│   │       ├── telegram.py # Telegram bot setup, handlers, interaction logic
│   │       └── whatsapp.py # Placeholder for WhatsApp integration logic
│   │
│   ├── knowledge/        # Interaction with knowledge base (Qdrant)
│   │   ├── __init__.py
│   │   ├── qdrant_manager.py # Qdrant client setup, collection ops, search/upsert (with RBAC)
│   │   └── document_processor.py # Logic for chunking, metadata extraction (used by scripts/)
│   │
│   ├── memory/           # Persistent memory and feedback handling
│   │   ├── __init__.py
│   │   ├── checkpointer.py # Setup for SqliteCheckpointer
│   │   └── feedback.py   # Functions init_feedback_db(), save_feedback()
│   │
│   ├── tools/            # LangChain Tool definitions
│   │   ├── __init__.py
│   │   └── crm_tools.py  # Defines @tool wrappers for CRM adapter methods
│   │   └── # (Add other tool files as needed)
│   │
│   └── utils/            # Common utility functions
│       ├── __init__.py
│       └── logging_config.py # Setup for Python logging module
│       └── # (Add other utilities like error handlers, formatters)
│
└── tests/                # Unit and integration tests
    ├── __init__.py
    ├── test_agent/
    ├── test_integrations/
    │   ├── test_crm/
    │   └── test_messengers/
    ├── test_knowledge/
    ├── test_memory/
    ├── test_tools/
    └── # (Mirror src structure where applicable)