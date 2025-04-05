import os
import sys
from typing import Dict, List, TypedDict, Union, Any, Annotated, Optional
from pydantic import BaseModel

sys.path.insert(1, os.path.join(sys.path[0], ".."))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.analyze_data import data_analyzer
from langgraph.generate_sql_query import generate_and_run_sql_query
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from prompt_templates.router_template import SYSTEM_PROMPT
from langgraph.checkpoint import FileSystemCheckpointer

load_dotenv()

# Define modern state management using TypedDict and Pydantic
class AgentState(TypedDict):
    messages: List[Union[HumanMessage, AIMessage, SystemMessage]]
    next: Optional[str]


# Set up tools 
tools = [generate_and_run_sql_query, data_analyzer]

# Using latest model with function calling
model = ChatOpenAI(model="gpt-4o", temperature=0).bind_tools(tools)


# Define the agent node with enhanced error handling
def agent(state: AgentState) -> Dict[str, Any]:
    """Agent node that processes messages and determines next actions"""
    messages = state["messages"]
    
    try:
        # Call the model with the current messages
        response = model.invoke(messages)
        return {"messages": messages + [response], "next": None}
    except Exception as e:
        # Error handling to make the agent more robust
        error_message = AIMessage(content=f"Error occurred: {str(e)}. Let me try a different approach.")
        return {"messages": messages + [error_message], "next": None}


# Define conditional routing based on tool calls or completion
def router(state: AgentState) -> str:
    """Route to the appropriate next node based on the latest message"""
    messages = state["messages"]
    last_message = messages[-1]
    
    # If there's an explicit next destination in state, use that
    if state.get("next"):
        return state["next"]
    
    # Check for tool calls in the last message
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    # End the conversation if no tool calls detected
    return END


def create_agent_graph(persist_dir: str = None) -> StateGraph:
    """Create a more advanced agent graph with persistence support"""
    # Initialize the graph with the enhanced state
    workflow = StateGraph(AgentState)
    
    # Add nodes for the main agent and tool execution
    workflow.add_node("agent", agent)
    workflow.add_node("tools", ToolNode(tools))
    
    # Define the workflow with conditional edges
    workflow.add_edge("agent", router)
    workflow.add_edge("tools", "agent")
    
    # Start with the agent node
    workflow.set_entry_point("agent")
    
    # Add checkpointing if a persistence directory is provided
    if persist_dir:
        checkpointer = FileSystemCheckpointer(persist_dir)
        return workflow.compile(checkpointer=checkpointer)
    
    return workflow.compile()


def run_agent(query: str, thread_id: str = None) -> str:
    """Run the agent with a specific query and optional thread_id for persistence"""
    # Set up persistence directory if thread_id is provided
    persist_dir = f"./threads/{thread_id}" if thread_id else None
    
    # Create the agent graph with optional persistence
    app = create_agent_graph(persist_dir)
    
    # Set up initial state with the query and system prompt
    initial_state = {
        "messages": [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=query)
        ],
        "next": None
    }
    
    # Configure with thread_id if provided for continuity
    config = {"configurable": {"thread_id": thread_id}} if thread_id else {}
    
    # Execute the workflow and extract the final response
    try:
        final_state = app.invoke(initial_state, config=config)
        response_messages = [m for m in final_state["messages"] if isinstance(m, AIMessage)]
        
        # Return the content of the last AI message or a fallback message
        if response_messages:
            return response_messages[-1].content
        return "No response generated."
    except Exception as e:
        return f"An error occurred while processing your request: {str(e)}"
