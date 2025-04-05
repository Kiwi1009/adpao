import os
import sys
import uuid
import argparse
from colorama import Fore, init

sys.path.insert(1, os.path.join(sys.path[0], ".."))
import gradio as gr
from langgraph.router import run_agent
from langgraph.router_web import run_real_estate_agent

def gradio_interface(message, history, mode="default"):
    """Enhanced Gradio interface with conversation persistence and mode switching"""
    # Generate a session ID based on the conversation history length
    # This is a simple way to maintain conversation continuity within a session
    session_id = str(uuid.uuid4()) if not history else f"session_{len(history)}"
    
    # Run the appropriate agent based on mode
    if mode == "real_estate":
        return run_real_estate_agent(message, thread_id=session_id)
    else:
        # Default to SQL/data analysis mode
        return run_agent(message, thread_id=session_id)

def launch_app():
    """Launch the Gradio app with mode selection"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="LangGraph Agent")
    parser.add_argument("--mode", type=str, choices=["default", "real_estate"], 
                      default="default", help="Agent mode: default (SQL/data) or real_estate")
    args = parser.parse_args()
    
    # Initialize colorama
    init()
    print(Fore.CYAN, f"\n\n[LangGraph] Initializing Gradio interface in {args.mode} mode\n")
    
    # Configure interface based on selected mode
    if args.mode == "real_estate":
        title = "LangGraph Real Estate Agent"
        description = "A real estate assistant that helps with property searches, mortgages, and neighborhood information."
        examples = [
            "What are typical home prices in Austin, Texas?",
            "Calculate mortgage payments for a $450,000 loan at 6.5% interest",
            "Tell me about schools and safety in the Downtown area"
        ]
    else:
        # Default SQL/data mode
        title = "LangGraph Agent (2024)"
        description = "An advanced LangGraph agent with persistent state management and enhanced error handling."
        examples = [
            "What were our total sales in Q1?",
            "Analyze the revenue trends for the past year",
            "Calculate 245 * 37"
        ]
    
    # Create a more informative interface
    interface = gr.ChatInterface(
        fn=lambda message, history: gradio_interface(message, history, args.mode),
        title=title,
        description=description,
        examples=examples,
        theme="soft"
    )
    
    # Launch with sharing disabled for security
    print(Fore.GREEN, f"\n\n[LangGraph] Launching Gradio interface in {args.mode} mode\n")
    interface.launch(share=False)

if __name__ == "__main__":
    # Create threads directory for persistence if it doesn't exist
    os.makedirs("./threads", exist_ok=True)
    os.makedirs("./threads/real_estate", exist_ok=True)
    launch_app()
