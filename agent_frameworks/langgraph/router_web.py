import os
import sys
import uuid
import asyncio
from typing import Dict, List, Any, Optional, Tuple

from dotenv import load_dotenv
from colorama import Fore, init

from tavily import TavilyClient
from langchain.tools import Tool

from typing import Literal

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.prebuilt import create_react_agent, ToolNode
from langchain_core.tools import tool
from langgraph.graph import MessagesState, END
from langgraph.types import Command
from langgraph.graph import StateGraph, START
from langchain_openai import ChatOpenAI


load_dotenv()
llm = ChatOpenAI()

class RealEstateRouter:
    @staticmethod
    def make_system_prompt(suffix: str) -> str:
        return (
            "You are a helpful AI assistant, collaborating with other assistants."
            " Use the provided tools to progress towards answering the question."
            " If you are unable to fully answer, that's OK, another assistant with different tools "
            " will help where you left off. Execute what you can to make progress."
            "Keep your final answer concise and to the point."
            " If you or any of the other assistants have the final answer or deliverable,"
            " prefix your response with FINAL ANSWER so the team knows to stop."
            f"\n{suffix}"
        )

    def __init__(self):
        init()

        try:
            # Get Tavily API key from environment
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            if not tavily_api_key:
                raise ValueError("TAVILY_API_KEY not found in environment variables")
            
            # Initialize Tavily client with API key from environment
            self.tavily_client = TavilyClient(api_key=tavily_api_key)
            
            # Create a proper tool function with decorator
            @tool
            def web_search(query: str) -> Dict[str, Any]:
                """Search the web for real estate information."""
                return self.tavily_client.search(query)
            
            # The line `self.web_search_tool = web_search` is initializing the `web_search_tool`
            # attribute of the `RealEstateRouter` class with the `web_search` function. This function
            # is a tool that searches the web for real estate information using the Tavily client. The
            # `web_search_tool` attribute is used as one of the tools available to the
            # `RealEstateRouter` for processing queries related to real estate.
            self.web_search_tool = web_search
            self.has_web_search = True
            print(Fore.GREEN, "\n\n[Real Estate SDK] Tavily WebSearchTool initialized successfully\n")
        except Exception as e:
            self.has_web_search = False
            self.web_search_tool = None
            print(Fore.RED, f"\n\n[Real Estate SDK] Error initializing Tavily WebSearchTool: {str(e)}\n")
            print(Fore.YELLOW, "\n\n[Real Estate SDK] Continuing without web search capability\n")
        
        # Create tool node with a list of tools
        tools = [self.web_search_tool]
        self.web_search_tool_node = ToolNode(tools)
        
        self.property_search_agent = create_react_agent(
            llm,
            tools=tools,  # Pass the same list of tools
            prompt=self.make_system_prompt(
                "You can search for housing or apartment listings online. You are working together with the real_estate_agent."
            ),
        )
        
        self.neighborhood_agent = create_react_agent(
            llm,
            tools=tools,  # Pass the same list of tools
            prompt=self.make_system_prompt(
                "You can search for specific characteristics of neighborhoods within a city. You are working together with the real_estate_agent."
            ),
        )
        
        self.real_estate_agent = create_react_agent(
            llm,
            tools=[],
            prompt=self.make_system_prompt(
                "You can only coordinate. You are working with the other agents."
            ),
        )
        
        
    
        workflow = StateGraph(MessagesState)
        workflow.add_node("real_estate_agent", self.real_estate_agent_node)
        workflow.add_node("property_search_agent", self.property_search_agent_node)

        workflow.add_edge(START, "real_estate_agent")
        self.graph = workflow.compile()
        
        print(Fore.GREEN, "\n\n[Real Estate SDK] All agents initialized successfully\n")
        

    # General system prompt for the agents
    def make_system_prompt(self, suffix: str) -> str:
        return (
            "You are a helpful AI assistant, collaborating with other assistants."
            " Use the provided tools to progress towards answering the question."
            " If you are unable to fully answer, that's OK, another assistant with different tools "
            " will help where you left off. Execute what you can to make progress."
            " If you or any of the other assistants have the final answer or deliverable,"
            " prefix your response with FINAL ANSWER so the team knows to stop."
            f"\n{suffix}"
        )


    # Any agent could decide the work is done
    @staticmethod
    def get_next_node(last_message: BaseMessage, goto: str):
        if "FINAL ANSWER" in last_message.content:
            # Any agent decided the work is done
            return END
        return goto




    def real_estate_agent_node(self, 
        state: MessagesState,
    ) -> Command[Literal["property_search_agent", END]]:
        print(Fore.CYAN + "\n[Real Estate Coordinator] Processing query..." + Fore.RESET)
        result = self.real_estate_agent.invoke(state)
        goto = RealEstateRouter.get_next_node(result["messages"][-1], "property_search_agent")
        
        if goto == END:
            print(Fore.GREEN + "[Real Estate Coordinator] Completed with final answer" + Fore.RESET)
        else:
            print(Fore.YELLOW + "[Real Estate Coordinator] Delegating to Property Search Agent" + Fore.RESET)
        
        result["messages"][-1] = HumanMessage(
            content=result["messages"][-1].content, name="real_estate_agent"
        )
        return Command(
            update={"messages": result["messages"]},
            goto=goto,
        )





    def property_search_agent_node(self, state: MessagesState) -> Command[Literal["real_estate_agent", END]]:
        print(Fore.BLUE + "\n[Property Search Agent] Searching for information..." + Fore.RESET)
        result = self.property_search_agent.invoke(state)
        goto = RealEstateRouter.get_next_node(result["messages"][-1], "real_estate_agent")
        
        if goto == END:
            print(Fore.GREEN + "[Property Search Agent] Completed with final answer" + Fore.RESET)
        else:
            print(Fore.YELLOW + "[Property Search Agent] Returning to Coordinator" + Fore.RESET)
        
        result["messages"][-1] = HumanMessage(
            content=result["messages"][-1].content, name="property_search_agent"
        )
        return Command(
            update={"messages": result["messages"]},
            goto=goto,
        )
    
    def neighborhood_agent_node(self, state: MessagesState) -> Command[Literal["real_estate_agent", END]]:
        print(Fore.BLUE + "\n[Property Search Agent] Searching for information..." + Fore.RESET)
        result = self.neighborhood_agent.invoke(state)
        goto = RealEstateRouter.get_next_node(result["messages"][-1], "real_estate_agent")
        
        if goto == END:
            print(Fore.GREEN + "[Neighborhood Agent] Completed with final answer" + Fore.RESET)
        else:
            print(Fore.YELLOW + "[Neighborhood Agent] Returning to Coordinator" + Fore.RESET)
        
        result["messages"][-1] = HumanMessage(
            content=result["messages"][-1].content, name="neighborhood_agent"
        )
        return Command(
            update={"messages": result["messages"]},
            goto=goto,
        )


    def _run_agent(self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Tuple[str, List[Dict[str, str]]]:
        print(Fore.MAGENTA + f"\n[Real Estate System] Starting new query: '{query}'" + Fore.RESET)
        if conversation_history is None:
            conversation_history = [{
                "role": "system",
                "content": (
                    "You are a comprehensive real estate assistant. Use your knowledge to answer general questions."
                )
            }]
        conversation_history.append({
            "role": "user",
            "content": query
        })
        
        conversation_history.append(HumanMessage(content=query))
        

        # Generate a unique session ID
        session_id = str(uuid.uuid4())


        try:
            # Stream the response
            response = ""
            for output in self.graph.stream(
                {"messages": conversation_history},
                {"configurable": {"session_id": session_id}},
                stream_mode="values"
            ):
                response += output["messages"][-1].content

            return response, conversation_history

        
        except Exception as e:
            error_msg = (
                "I apologize, but I'm currently experiencing some technical difficulties. "
                "Could you please rephrase your question or ask something about real estate concepts?"
            )
            return error_msg, conversation_history

    def process_query(self, query: str, thread_id: Optional[str] = None) -> str:
        try:
            response, _ = self._run_agent(query)
            return response
        except Exception as e:
            return (
                "I apologize, but I'm experiencing technical difficulties. "
                "Please try again later."
            )
