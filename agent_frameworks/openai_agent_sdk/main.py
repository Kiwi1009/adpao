import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], ".."))

import gradio as gr
from router import AgentRouter

def gradio_interface(message, history):
    router = AgentRouter()
    agent_response = router.process_query(message)
    return agent_response

def launch_app():
    iface = gr.ChatInterface(fn=gradio_interface, title="OpenAI Agent SDK")
    iface.launch()

if __name__ == "__main__":
    launch_app() 