"""Node for executing tools called by the LLM."""

import logging
from typing import Dict, List, Optional, Callable, Any

# ToolMessage is used to structure the output of tool calls for the LLM
from langchain_core.messages import ToolMessage, BaseMessage

from src.agent.state import AgentState
# Import the actual tool functions that can be called
from src.tools.crm_tools import get_crm_customer_info

logger = logging.getLogger(__name__)

# --- Tool Mapping --- 

# Map tool names (as the LLM knows them) to their actual functions
# Ensure the names match how the LLM is expected to call them (often the function name)
_tool_map: Dict[str, Callable[..., Any]] = {
    "get_crm_customer_info": get_crm_customer_info,
    # Add other tool functions here as they are created
    # "another_tool_name": another_tool_function,
}

# --- Node Function --- 

def execute_tools(state: AgentState) -> Dict[str, List[BaseMessage]]:
    """
    Executes the tools requested by the LLM in the previous step.

    Retrieves tool calls from the state, executes the corresponding functions
    using the provided arguments, and formats the results as ToolMessage objects.

    Args:
        state: The current state of the agent graph, containing potential tool_calls.

    Returns:
        A dictionary containing the update for the 'messages' key in the state.
        The value is a list of ToolMessage objects representing the results,
        which will be appended to the existing message history.
        Returns an empty dictionary if no tool calls were present.
    """
    logger.info("---NODE: tool_executor---")
    tool_calls = state.get('tool_calls')

    if not tool_calls:
        logger.info("No tool calls to execute.")
        # If no tools to run, return no state updates (implicitly keeps existing messages)
        # Returning {"messages": state['messages']} would also work but is redundant
        return {} # No changes to messages if no tools called

    tool_outputs: List[BaseMessage] = []
    for tool_call in tool_calls:
        tool_name = tool_call.get('name')
        tool_args = tool_call.get('args', {})
        tool_call_id = tool_call.get('id') # Crucial for matching output to call

        if not tool_call_id:
            logger.error(f"Tool call missing required 'id'. Skipping: {tool_call}")
            continue # Skip calls without an ID

        logger.info(f"Attempting to execute tool: {tool_name} with args: {tool_args} (ID: {tool_call_id})")

        tool_function = _tool_map.get(tool_name)

        if tool_function:
            try:
                # Execute the tool function with the arguments provided by the LLM
                output = tool_function(**tool_args)
                logger.info(f"Tool '{tool_name}' executed successfully. Output: {str(output)[:100]}...")
                tool_outputs.append(
                    ToolMessage(content=str(output), tool_call_id=tool_call_id)
                )
            except Exception as e:
                logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
                # Report the error back to the LLM
                error_content = f"Error executing tool '{tool_name}': {type(e).__name__} - {e}"
                tool_outputs.append(
                    ToolMessage(content=error_content, tool_call_id=tool_call_id)
                )
        else:
            logger.error(f"Tool '{tool_name}' not found in tool map.")
            # Report that the tool wasn't found
            error_content = f"Error: Tool '{tool_name}' not found."
            tool_outputs.append(
                ToolMessage(content=error_content, tool_call_id=tool_call_id)
            )

    # Return the list of ToolMessages to be appended to the state's messages list
    # LangGraph automatically merges list updates for keys like 'messages'
    return {"messages": tool_outputs} 