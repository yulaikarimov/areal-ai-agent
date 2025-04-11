"""Defines the core workflow graph for the AI agent using LangGraph, \
connecting nodes and compiling with persistent memory."""

import logging
import asyncio # Import asyncio
from typing import Dict, Optional, Any

# StateGraph is the main class for defining the workflow
# END is a special node marker to indicate the end of the graph execution
from langgraph.graph import StateGraph, END

from src.agent.state import AgentState
# Import the actual node functions from their respective modules
from src.agent.nodes.retrieval import retrieve_documents
from src.agent.nodes.generation import generator
from src.agent.nodes.routing import route_tools
from src.agent.nodes.tool_execution import execute_tools
# Import the checkpointer context factory function
from src.memory.checkpointer import get_checkpointer_context
# Import the actual saver type for type hinting
from langgraph_checkpoint_sqlite import AsyncSqliteSaver 

logger = logging.getLogger(__name__)

# --- Graph Definition --- 

# Initialize the state graph with the AgentState structure
workflow = StateGraph(AgentState)

# Add the actual nodes to the graph, linking names to imported functions
logger.info("Adding nodes to the graph...")
workflow.add_node("retriever", retrieve_documents)
workflow.add_node("generator", generator)
workflow.add_node("tool_executor", execute_tools)
logger.info("Nodes added.")

# --- Edge Definitions --- 

logger.info("Defining graph edges...")
# Set the entry point: the first node to execute
workflow.set_entry_point("retriever")

# Define the standard flow edges
workflow.add_edge("retriever", "generator")
workflow.add_edge("tool_executor", "generator")

# Define the conditional edge after generation: route to tools or end
workflow.add_conditional_edges(
    "generator", # Source node
    route_tools, # CORRECT NAME Function that returns the next node name ("tool_executor" or "__end__")
    {
        # Map the return value of route_to_tools_or_generate to the target node name
        "tool_executor": "tool_executor", 
        "__end__": END # Map "__end__" to the predefined END marker
    }
)
logger.info("Edges defined.")

# --- Compile the Graph --- 

# Define an async function to compile the graph
# It now takes the instantiated checkpointer as an argument
async def compile_graph(checkpointer: Optional[AsyncSqliteSaver]) -> Optional[Any]:
    """Compiles the LangGraph workflow using the provided checkpointer."""
    logger.info("Attempting to compile the agent graph...")
    
    try:
        if checkpointer:
            graph = workflow.compile(checkpointer=checkpointer)
            logger.info("Agent graph compiled successfully WITH provided checkpointer.")
        else:
            graph = workflow.compile()
            logger.warning("Agent graph compiled WITHOUT checkpointer (None provided). Memory will be ephemeral.")
        return graph
    except ImportError as ie:
        logger.error(f"Failed to compile graph due to import error: {ie}. Is langgraph or a dependency installed correctly?", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Failed to compile agent graph: {e}", exc_info=True)
        return None

# --- Get the Compiled Graph --- 

# Define agent_graph at module level, it will be assigned during app initialization
agent_graph: Optional[Any] = None 

# Note: We will NOT compile the graph here at import time. 
# Instead, the main application entry point (e.g., main.py or telegram.py)
# should call `await compile_graph()` during its asynchronous setup phase
# and assign the result to this module's `agent_graph` variable or pass it around.

# Example (This should be done in the main async execution context, not here):
# async def initialize_app():
#     global agent_graph
#     agent_graph = await compile_graph()
#     if agent_graph is None:
#        logger.critical("Agent graph compilation failed. The agent cannot run.")
#        # Handle fatal error

# Remove the old synchronous compilation block
# logger.info("Compiling the agent graph...")
# agent_graph: Optional[Any] = None # Define variable upfront
# try:
#     ...
# except ...
# if agent_graph is None:
#     ... 