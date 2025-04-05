import os
import sys
from colorama import Fore, init

sys.path.insert(1, os.path.join(sys.path[0], ".."))

import gradio as gr
from router import SwarmRouter

def gradio_interface(message, history):
    router = SwarmRouter()
    agent_response = router.process_query(message)
    return agent_response

def launch_app():
    # Initialize colorama for cross-platform colored terminal output
    init()
    print(Fore.CYAN, "\n\n[OpenAI Swarms Agent] Initializing Gradio interface\n")
    
    iface = gr.ChatInterface(
        fn=gradio_interface, 
        title="OpenAI Swarms Agent",
        description="A multi-agent system using OpenAI Swarms for SQL queries and data analysis."
    )
    
    print(Fore.GREEN, "\n\n[OpenAI Swarms Agent] Launching Gradio interface\n")
    iface.launch()

if __name__ == "__main__":
    launch_app() 