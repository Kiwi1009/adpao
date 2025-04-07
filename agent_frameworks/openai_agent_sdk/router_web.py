import os
import sys
import asyncio
import uuid
from typing import Dict, List, Any
from colorama import Fore, init

sys.path.insert(1, os.path.join(sys.path[0], ".."))

from dotenv import load_dotenv
from agents import Agent, Runner, WebSearchTool

load_dotenv()

class RealEstateRouter:
    def __init__(self):
        """
        Initialize the Real Estate Router with specialized agents for property search,
        mortgages, and neighborhood information.
        """
        # Initialize colorama for cross-platform colored terminal output
        init()
        
        # Initialize web search tool with error handling
        try:
            self.web_search = WebSearchTool()
            self.has_web_search = True
            print(Fore.GREEN, "\n\n[Real Estate SDK] WebSearchTool initialized successfully\n")
        except Exception as e:
            self.has_web_search = False
            print(Fore.RED, f"\n\n[Real Estate SDK] Error initializing WebSearchTool: {str(e)}\n")
            print(Fore.YELLOW, "\n\n[Real Estate SDK] Continuing without web search capability\n")
        
        # Create specialized agents
        self.property_search_agent = self._create_property_search_agent()
        self.mortgage_agent = self._create_mortgage_agent()
        self.neighborhood_agent = self._create_neighborhood_agent()
        
        # Create the main orchestrator agent
        self.real_estate_agent = self._create_real_estate_agent()
        
        print(Fore.GREEN, "\n\n[Real Estate SDK] All agents initialized successfully\n")
        
    def _create_property_search_agent(self) -> Agent:
        """Create an agent specialized in property search"""
        print(Fore.GREEN, "\n\n[Real Estate SDK] Creating Property Search agent\n")
        
        instructions = """
            You are a real estate property search specialist.

            When asked about properties or homes for sale, use your knowledge to provide information.
            
            Return the information in a clear, structured format.

            Always include if available:
            - Property address
            - Listing price
            - Number of bedrooms and bathrooms
            - Square footage
            - Property type

            After providing property listings, ask ONE specific follow-up question to learn more about the user's
            preferences, budget constraints, or must-have features. This will help you provide more targeted property recommendations.
        """
        
        # Add web search only if available
        tools = []
        if self.has_web_search:
            instructions = """
                You are a real estate property search specialist.

                When asked about properties or homes for sale, use the web_search tool to find current listings.
                Return the information in a clear, structured format.

                Always include if available:
                - Property address
                - Listing price
                - Number of bedrooms and bathrooms
                - Square footage
                - Property type
                - URL to the actual listing (must be real URLs from your web search, never use example.com or placeholder URLs)

                After providing property listings, ask ONE specific follow-up question to learn more about the user's
                preferences, budget constraints, or must-have features. This will help you provide more targeted property recommendations.
                
                If web search fails, politely explain that you're currently unable to access real-time listing data,
                but can still discuss general property information for the area based on your knowledge.
            """
            tools = [self.web_search]
            
        return Agent(
            name="property_search_agent",
            instructions=instructions,
            tools=tools,
        )
    
    def _create_mortgage_agent(self) -> Agent:
        """Create an agent specialized in mortgages"""
        print(Fore.GREEN, "\n\n[Real Estate SDK] Creating Mortgage agent\n")
        
        instructions = """
            You are a mortgage specialist.

            Provide information about mortgage options, financing strategies, and loan considerations
            based on your knowledge of the real estate market.
            
            Consider the user's budget, down payment capabilities, and financial goals.

            Always include when possible:
            - Loan amount options
            - General interest rate ranges
            - Estimated monthly payments
            - Recommended down payment

            After providing mortgage information, ask ONE specific follow-up question to learn more about the user's
            financial situation, credit score range, or long-term housing plans. This will help you provide more accurate mortgage advice.
        """
        
        # Add web search only if available
        tools = []
        if self.has_web_search:
            instructions = """
                You are a mortgage specialist.

                When asked about mortgages, financing, or home loans, use the web_search tool to find current rates and information.
                Consider the user's budget, down payment capabilities, and financial goals.

                Always include when possible:
                - Loan amount options
                - Current interest rates
                - Estimated monthly payments
                - Recommended down payment

                After providing mortgage information, ask ONE specific follow-up question to learn more about the user's
                financial situation, credit score range, or long-term housing plans. This will help you provide more accurate mortgage advice.
                
                If web search fails, politely explain that you're currently unable to access real-time mortgage rate data,
                but can still discuss general mortgage concepts and strategies based on your knowledge.
            """
            tools = [self.web_search]
            
        return Agent(
            name="mortgage_agent",
            instructions=instructions,
            tools=tools,
        )
    
    def _create_neighborhood_agent(self) -> Agent:
        """Create an agent specialized in neighborhood information"""
        print(Fore.GREEN, "\n\n[Real Estate SDK] Creating Neighborhood agent\n")
        
        instructions = """
            You are a neighborhood information specialist.

            Provide details about neighborhoods and locations based on your knowledge.
            Focus on details about schools, amenities, safety, and transportation options.

            Always include when possible:
            - School information
            - Local amenities (parks, shopping, restaurants)
            - General safety information
            - Public transportation options and walkability

            After providing neighborhood information, ask ONE specific follow-up question to understand if the user
            has specific concerns about the area or particular amenities they're looking for. This will help you provide more relevant information.
        """
        
        # Add web search only if available
        tools = []
        if self.has_web_search:
            instructions = """
                You are a neighborhood information specialist.

                When asked about neighborhoods or locations, use the web_search tool to find relevant information.
                Provide details about schools, amenities, safety, and transportation options.

                Always include when possible:
                - School ratings and districts
                - Local amenities (parks, shopping, restaurants)
                - Crime statistics and safety information
                - Public transportation options and walkability

                After providing neighborhood information, ask ONE specific follow-up question to understand if the user
                has specific concerns about the area or particular amenities they're looking for. This will help you provide more relevant information.
                
                If web search fails, politely explain that you're currently unable to access real-time neighborhood data,
                but can still discuss general information about the area based on your knowledge.
            """
            tools = [self.web_search]
            
        return Agent(
            name="neighborhood_agent",
            instructions=instructions,
            tools=tools,
        )
    
    def _create_real_estate_agent(self) -> Agent:
        """Create the main real estate orchestrator agent"""
        print(Fore.GREEN, "\n\n[Real Estate SDK] Creating main Real Estate agent\n")
        
        # Base instructions for no web search
        instructions = """
            You are a comprehensive real estate assistant that helps users find properties,
            understand mortgage options, and learn about neighborhoods.

            IMPORTANT: When specific current information is needed:
            1. For specific property listings or homes for sale → hand off to property_search_agent
            2. For current mortgage rates and specific financing calculations → hand off to mortgage_agent
            3. For specific neighborhood data or current local information → hand off to neighborhood_agent
            
            Make sure you keep the information about past querries.

        """
            
        return Agent(
            name="real_estate_agent",
            instructions=instructions,
            handoffs=[self.property_search_agent, self.mortgage_agent, self.neighborhood_agent],
        )
    
    async def _run_agent(self, query: str, conversation_history=None) -> str:
        """Run the appropriate agent with the user query"""
        print(Fore.MAGENTA, f"\n\n[Real Estate SDK] Processing query: {query}\n")
        
        # Initialize or update conversation history
        if conversation_history is None:
            conversation_history = [{
                "role": "system",
                "content": """You are a comprehensive real estate assistant. Use your knowledge to answer general questions.
                Only use web search when specific current information (like property listings, rates, or neighborhood data) is needed."""
            }]
        
        # Add user query to conversation
        new_input = conversation_history + [{"role": "user", "content": query}]
        
        try:
            # Run the agent
            print(Fore.BLUE, f"\n\n[Real Estate SDK] Running real estate agent\n")
            
            # Track if handoff is attempted
            print(Fore.WHITE, f"\n[Real Estate SDK] Checking if handoff is needed...")
            
            result = await Runner.run(self.real_estate_agent, new_input)
            
            # Log which specialized agent was used (if any)
            if hasattr(result, 'last_agent') and result.last_agent and result.last_agent.name != "real_estate_agent":
                print(Fore.YELLOW, f"\n[Real Estate SDK] Handoff detected!")
                print(Fore.YELLOW, f"[Real Estate SDK] ⮕ Query was handled by: {result.last_agent.name}")
            else:
                print(Fore.CYAN, "\n[Real Estate SDK] No handoff needed - Query handled by main real estate agent")
            
            # Extract response
            response = result.final_output
            print(Fore.GREEN, f"\n\n[Real Estate SDK] Agent response: {response[:100]}...\n")
            
            return response, result.to_input_list()
            
        except Exception as e:
            error_msg = f"I apologize, but I'm currently experiencing some technical difficulties with my real-time data access. I can still help you with general real estate questions based on my knowledge. Could you please rephrase your question or ask something about real estate concepts, market trends, or general advice?"
            print(Fore.RED, f"\n\n[Real Estate SDK] Error: {str(e)}\n")
            
            # Return a user-friendly error message and the original conversation history
            return error_msg, conversation_history
    
    def process_query(self, query: str) -> str:
        """
        Process a user query using the real estate agent system
        This is the main entry point that matches the interface expected by the main.py file
        """
        print(Fore.CYAN, f"\n\n[Real Estate SDK] Received query: {query}\n")
        
        # Create a unique session ID for this conversation
        session_id = str(uuid.uuid4())
        print(Fore.YELLOW, f"\n\n[Real Estate SDK] Session ID: {session_id}\n")
        
        # We need to run the async function in a synchronous context for Gradio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run the agent and get the response
            response, _ = loop.run_until_complete(self._run_agent(query))
        except Exception as e:
            # Catch any uncaught exceptions and return a friendly error message
            print(Fore.RED, f"\n\n[Real Estate SDK] Critical error: {str(e)}\n")
            response = "I apologize, but I'm experiencing technical difficulties at the moment. Please try again later or ask me a general real estate question that doesn't require accessing external data."
        finally:
            loop.close()
        
        return response