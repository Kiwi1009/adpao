import os
import sys
from typing import Dict, List, Any

sys.path.insert(1, os.path.join(sys.path[0], ".."))

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.beta.assistant import Assistant
from openai.types.beta.thread import Thread
from openai.types.beta.threads.run import Run
from prompt_templates.router_template import SYSTEM_PROMPT
from skills.skill_map import SkillMap

load_dotenv()

class AgentRouter:
    def __init__(self):
        """
        Initialize the OpenAI Agent SDK router with assistants for SQL queries and data analysis.
        """
        self.client = OpenAI()
        self.skill_map = SkillMap()
        
        # Create the SQL assistant for database operations
        self.sql_assistant = self._create_sql_assistant()
        
        # Create the analyzer assistant for data insights
        self.data_analyzer = self._create_data_analyzer()
        
        # Create the main assistant that routes queries
        self.router_assistant = self._create_router_assistant()
        
    def _create_sql_assistant(self) -> Assistant:
        """Create an assistant specialized in SQL queries"""
        sql_tools = [{"type": "function", "function": self.skill_map.get_function_schema_by_name("generate_and_run_sql_query")}]
        
        return self.client.beta.assistants.create(
            name="SQL Expert",
            instructions="You generate and execute SQL queries based on user requests to extract data from databases.",
            tools=sql_tools,
            model="gpt-4-turbo-preview"
        )
    
    def _create_data_analyzer(self) -> Assistant:
        """Create an assistant specialized in data analysis"""
        analysis_tools = [{"type": "function", "function": self.skill_map.get_function_schema_by_name("data_analyzer")}]
        
        return self.client.beta.assistants.create(
            name="Data Analyzer",
            instructions="You analyze data and provide insights based on SQL query results.",
            tools=analysis_tools,
            model="gpt-4-turbo-preview"
        )
    
    def _create_router_assistant(self) -> Assistant:
        """Create the main router assistant to handle initial query classification"""
        return self.client.beta.assistants.create(
            name="Router",
            instructions=SYSTEM_PROMPT,
            model="gpt-4-turbo-preview"
        )
    
    def _create_thread(self) -> Thread:
        """Create a new conversation thread"""
        return self.client.beta.threads.create()
    
    def _run_assistant(self, assistant_id: str, thread_id: str, user_message: str) -> str:
        """
        Run an assistant with a user message and return the response
        """
        # Add user message to thread
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )
        
        # Run the assistant
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        
        # Wait for completion
        run = self._wait_for_run(thread_id, run.id)
        
        # Get and return the latest assistant response
        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
        for message in messages.data:
            if message.role == "assistant":
                # Return the first assistant message (most recent)
                content = message.content[0].text.value if message.content else "No response generated."
                return content
        
        return "No response generated."
    
    def _wait_for_run(self, thread_id: str, run_id: str) -> Run:
        """Wait for a run to complete and handle any needed function calls"""
        while True:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            
            if run.status == "completed":
                return run
            
            if run.status == "requires_action":
                self._handle_required_actions(thread_id, run_id, run.required_action)
            
            # For other statuses, wait before checking again
            import time
            time.sleep(1)
    
    def _handle_required_actions(self, thread_id: str, run_id: str, required_action: Any) -> None:
        """Handle function calls required by the assistant"""
        if not required_action or not required_action.submit_tool_outputs:
            return
        
        tool_outputs = []
        
        for tool_call in required_action.submit_tool_outputs.tool_calls:
            function_name = tool_call.function.name
            function_args = tool_call.function.arguments
            
            # Execute function from skill map
            result = self.skill_map.execute_function(
                function_name=function_name,
                function_args=function_args
            )
            
            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": result
            })
        
        # Submit the results back to the assistant
        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs
        )
    
    def process_query(self, query: str) -> str:
        """
        Process a user query using the appropriate assistant
        """
        # Create a new conversation thread
        thread = self._create_thread()
        
        # First, use the router to determine the type of query
        router_response = self._run_assistant(
            assistant_id=self.router_assistant.id,
            thread_id=thread.id,
            user_message=f"Classify this query and decide which assistant should handle it: {query}"
        )
        
        # Check router response to determine which assistant to use
        if "SQL" in router_response or "database" in router_response.lower():
            # SQL query - use SQL assistant
            return self._run_assistant(
                assistant_id=self.sql_assistant.id,
                thread_id=thread.id,
                user_message=query
            )
        elif "analysis" in router_response.lower() or "analyze" in router_response.lower():
            # Data analysis - use data analyzer
            return self._run_assistant(
                assistant_id=self.data_analyzer.id,
                thread_id=thread.id,
                user_message=query
            )
        else:
            # Default to the router's response if classification is unclear
            return router_response 