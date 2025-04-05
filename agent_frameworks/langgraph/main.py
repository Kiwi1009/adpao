import os
import sys
import uuid

sys.path.insert(1, os.path.join(sys.path[0], ".."))
import gradio as gr
from langgraph.router import run_agent

def gradio_interface(message, history):
    """Enhanced Gradio interface with conversation persistence"""
    # Generate a session ID based on the conversation history length
    # This is a simple way to maintain conversation continuity within a session
    session_id = str(uuid.uuid4()) if not history else f"session_{len(history)}"
    
    # Run the agent with the message and session ID for persistence
    return run_agent(message, thread_id=session_id)

def launch_app():
    """Launch the Gradio app with enhanced features"""
    # Create a more informative interface
    interface = gr.ChatInterface(
        fn=gradio_interface,
        title="LangGraph Agent (2024)",
        description="An advanced LangGraph agent with persistent state management and enhanced error handling.",
        examples=[
            "What were our total sales in Q1?",
            "Analyze the revenue trends for the past year",
            "Calculate 245 * 37"
        ],
        theme="soft"
    )
    
    # Launch with sharing disabled for security
    interface.launch(share=False)

if __name__ == "__main__":
    # Create threads directory for persistence if it doesn't exist
    os.makedirs("./threads", exist_ok=True)
    launch_app()
