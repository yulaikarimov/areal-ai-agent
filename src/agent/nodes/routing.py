"""Node for routing logic within the agent graph, specifically for tool usage."""

import logging
from typing import Literal

from src.agent.state import AgentState

logger = logging.getLogger(__name__)


def route_tools(state: AgentState) -> Literal["tool_executor", "__end__"]:
    """
    Determines the next step based on whether the LLM requested tool calls.

    Checks the 'tool_calls' key in the state. If it contains tool calls,
    routes the graph to the 'tool_executor' node. Otherwise, ends the graph execution.

    Args:
        state: The current state of the agent graph.

    Returns:
        A literal string indicating the next node: "tool_executor" or "__end__".
    """
    logger.info("---NODE: tool_router---")
    tool_calls = state.get('tool_calls') # Use .get for safety

    if tool_calls and len(tool_calls) > 0:
        logger.info(f"Решение маршрутизации: Есть вызовы инструментов ({len(tool_calls)} вызовов). Перехожу к выполнению инструментов.")
        # Return the name of the node that handles tool execution
        return "tool_executor"
    else:
        logger.info("Решение маршрутизации: Нет вызовов инструментов. Завершаю выполнение.")
        # Return the special value to end the graph execution
        return "__end__" 