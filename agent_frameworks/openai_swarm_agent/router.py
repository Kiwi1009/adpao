import os
import sys
from typing import Dict, List
from colorama import Fore, init

sys.path.insert(1, os.path.join(sys.path[0], ".."))

from dotenv import load_dotenv
from prompt_templates.router_template import SYSTEM_PROMPT
from skills.skill_map import SkillMap
from swarm import Agent, Swarm

load_dotenv()

class SwarmRouter:
    def __init__(self):
        # Initialize colorama for cross-platform colored terminal output
        init()
        
        self.client = Swarm()
        self.skill_map = SkillMap()
        
        # Create the analyzer agent for data analysis
        self.analyzer_agent = Agent(
            name="Data Analyzer",
            instructions="You analyze data and provide insights based on SQL query results.",
            functions=[self.skill_map.get_function_callable_by_name("data_analyzer")]
        )
        print(Fore.GREEN, "\n\n[Swarm Agent] Created Data Analyzer agent\n")
        
        # Create the SQL agent for query generation
        self.sql_agent = Agent(
            name="SQL Expert",
            instructions="You generate and execute SQL queries based on user requests.",
            functions=[
                self.skill_map.get_function_callable_by_name("generate_and_run_sql_query"),
                self.transfer_to_analyzer
            ]
        )
        print(Fore.GREEN, "\n\n[Swarm Agent] Created SQL Expert agent\n")
        
        # Create the router agent that decides which agent to use
        self.router_agent = Agent(
            name="Router",
            instructions=SYSTEM_PROMPT,
            functions=[
                self.transfer_to_sql,
                self.transfer_to_analyzer
            ]
        )
        print(Fore.GREEN, "\n\n[Swarm Agent] Created Router agent\n")

    def transfer_to_sql(self):
        print(Fore.YELLOW, "\n\n[Swarm Agent] Transferring to SQL Expert agent\n")
        return self.sql_agent
        
    def transfer_to_analyzer(self):
        print(Fore.YELLOW, "\n\n[Swarm Agent] Transferring to Data Analyzer agent\n")
        return self.analyzer_agent
        
    def process_query(self, query: str) -> str:
        print(Fore.CYAN, f"\n\n[Swarm Agent] Received query: {query}\n")
        
        print(Fore.MAGENTA, "\n\n[Swarm Agent] Starting router agent to process query\n")
        response = self.client.run(
            agent=self.router_agent,
            messages=[{"role": "user", "content": query}]
        )
        
        result = response.messages[-1]["content"]
        print(Fore.BLUE, f"\n\n[Swarm Agent] Final response: {result[:100]}...\n")
        
        return result 