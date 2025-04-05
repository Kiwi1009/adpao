import os
import sys
import argparse
from colorama import Fore, init

sys.path.insert(1, os.path.join(sys.path[0], ".."))

import gradio as gr
from router import AgentRouter
from router_web import RealEstateRouter

def gradio_interface(message, history, router_type="default"):
    # Initialize the appropriate router based on user selection
    if router_type == "real_estate":
        router = RealEstateRouter()
    else:  # default to original data/SQL router
        router = AgentRouter()
    
    agent_response = router.process_query(message)
    return agent_response

def launch_app():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="OpenAI Agent SDK")
    parser.add_argument("--mode", type=str, choices=["default", "real_estate"], 
                      default="default", help="Agent mode: default (SQL/data) or real_estate")
    args = parser.parse_args()
    
    # Initialize colorama for cross-platform colored terminal output
    init()
    print(Fore.CYAN, f"\n\n[OpenAI Agent SDK] Initializing Gradio interface in {args.mode} mode\n")
    
    # Title and description based on mode
    if args.mode == "real_estate":
        title = "OpenAI Agent SDK - Real Estate Assistant"
        description = "A real estate assistant that helps with property searches, mortgages, and neighborhood information."
        examples = [
            "What are current home prices in San Francisco?",
            "Can you help me find mortgage rates for a $500,000 loan?",
            "Tell me about schools in Austin, Texas"
        ]
    else:
        title = "OpenAI Agent SDK"
        description = "An agent using OpenAI Assistants API with specialized assistants for SQL queries and data analysis."
        examples = [
            "Show me total sales by region from the database",
            "Analyze customer trends from last quarter",
            "What were our top 5 products last year?"
        ]
    
    # Create Gradio interface with partial function to pass router_type
    iface = gr.ChatInterface(
        fn=lambda message, history: gradio_interface(message, history, args.mode), 
        title=title,
        description=description,
        examples=examples,
        theme="soft"
    )
    
    print(Fore.GREEN, f"\n\n[OpenAI Agent SDK] Launching Gradio interface in {args.mode} mode\n")
    iface.launch()

if __name__ == "__main__":
    launch_app() 