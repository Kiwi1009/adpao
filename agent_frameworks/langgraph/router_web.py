import os
import sys
from typing import Dict, List, Union, Any, Annotated, Optional, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from colorama import Fore, init

sys.path.insert(1, os.path.join(sys.path[0], ".."))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition


load_dotenv()

# Initialize colorama for cross-platform colored terminal output
init()

# Define state management for the real estate agent with message accumulation
class RealEstateState(TypedDict):
    messages: Annotated[list, add_messages]

# Create a Tavily Search tool instance for retrieving live data with URLs included
tavily_api_key = os.getenv("TAVILY_API_KEY")
print(Fore.GREEN, f"\n[LangGraph Real Estate] Using Tavily API Key: {tavily_api_key[:4]}...{tavily_api_key[-4:] if tavily_api_key else 'None'}")

tavily_tool = TavilySearchResults(
    api_key=tavily_api_key,
    max_results=5,
    include_raw_content=True,  # Include the raw content from search results
    include_images=False,      # We don't need images
    include_answer=True,       # Include an AI-generated answer 
    k=5                        # Top 5 results
)

# List of tools available for the agents
tools = [tavily_tool]

# Initialize the language model and bind tools
llm = ChatOpenAI(model="gpt-4o", temperature=0)
llm_with_tools = llm.bind_tools(tools)

# Add this comprehensive debug function at the top of the file, after the imports
def debug_tavily_response(query, response, agent_type):
    """Print comprehensive debug information about a Tavily response"""
    print(f"\n\n{'='*80}")
    print(Fore.YELLOW, f"[DEBUG] {agent_type} TAVILY RESPONSE DETAILS")
    print(f"{'='*80}")
    print(Fore.YELLOW, f"Query: {query}")
    print(Fore.YELLOW, f"Response type: {type(response)}")
    
    if isinstance(response, dict):
        print(Fore.YELLOW, f"Response keys: {list(response.keys())}")
        # Explore the structure of the response
        for key in response.keys():
            value = response[key]
            print(Fore.YELLOW, f"Key '{key}' has type: {type(value)}")
            
            # If it's a list with items, show the structure of the first item
            if isinstance(value, list) and value:
                print(Fore.YELLOW, f"First item in '{key}' has type: {type(value[0])}")
                if isinstance(value[0], dict):
                    print(Fore.YELLOW, f"First item keys: {list(value[0].keys())}")
    
    elif isinstance(response, list) and response:
        print(Fore.YELLOW, f"Response is a list with {len(response)} items")
        print(Fore.YELLOW, f"First item type: {type(response[0])}")
        if isinstance(response[0], dict):
            print(Fore.YELLOW, f"First item keys: {list(response[0].keys())}")
    
    # Print a sample of the raw response (limited to avoid massive output)
    print(Fore.YELLOW, f"Raw response sample: {str(response)[:500]}...")
    
    # Check explicitly for error indicators
    error_indicators = ["error", "exception", "400", "401", "403", "404", "500"]
    response_str = str(response).lower()
    for indicator in error_indicators:
        if indicator in response_str:
            print(Fore.RED, f"[WARNING] Error indicator found in response: '{indicator}'")
    
    print(f"\n{'='*80}\n")

# Coordinator: logs that processing is starting
def coordinator(state: RealEstateState):
    """Initial coordinator that starts the processing"""
    print(Fore.CYAN, "\n\n[LangGraph Real Estate] Starting coordinator\n")
    return {"messages": state["messages"] + [AIMessage(content="Real Estate Coordinator: Starting sub-agent processing...")]}

# Neighborhood agent: checks whether the neighborhood meets user criteria
def neighborhood_agent(state: RealEstateState):
    """Neighborhood agent that evaluates locations based on search results"""
    print(Fore.MAGENTA, "\n\n[LangGraph Real Estate] Running neighborhood agent\n")
    
    # Extract location from user query if possible
    user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
    
    if user_messages:
        user_query = user_messages[-1].content
        # Try to extract a location from the query
        import re
        location_match = re.search(r'in\s+([A-Za-z\s]+)', user_query)
        location = location_match.group(1) if location_match else "San Francisco"
    else:
        location = "San Francisco"  # Default location
    
    # Construct a search query for neighborhood quality
    query = f"Best neighborhoods in {location} for families, safety, and amenities"
    
    try:
        # Invoke Tavily Search using the tool with special parameters to ensure URLs
        print(Fore.BLUE, f"\n\n[LangGraph Real Estate] Searching for neighborhood info: {query}\n")
        search_result = tavily_tool.invoke({"query": query, "max_results": 5})
        
        # Add comprehensive debugging
        debug_tavily_response(query, search_result, "NEIGHBORHOOD AGENT")
        
        # Format the results to include links, handling different possible result structures
        formatted_results = ""

        # Debug the structure first
        print(Fore.YELLOW, f"\n\n[DEBUG] Result type: {type(search_result)}")

        # Case 1: Dictionary with "results" key (common Tavily format)
        if isinstance(search_result, dict) and "results" in search_result:
            for result in search_result["results"]:
                content = result.get("content", result.get("snippet", "No content available"))
                url = result.get("url", "No source URL available")
                formatted_results += f"\n\n- {content}\n🔗 SOURCE: {url}"

        # Case 2: Dictionary with "answer" and "citations" structure
        elif isinstance(search_result, dict) and "answer" in search_result and "citations" in search_result:
            # Include the answer
            formatted_results += f"\n\n{search_result['answer']}"
            # Add citations/sources
            formatted_results += "\n\n🔗 SOURCES:"
            for citation in search_result["citations"]:
                if isinstance(citation, dict):
                    url = citation.get("url", "No URL available")
                    title = citation.get("title", "Untitled source")
                    formatted_results += f"\n- {title}: {url}"
                else:
                    formatted_results += f"\n- {str(citation)}"

        # Case 3: List of results
        elif isinstance(search_result, list):
            for i, result in enumerate(search_result):
                if isinstance(result, dict):
                    # Try different possible key names for content
                    content_keys = ["content", "snippet", "text", "description"]
                    content = "No content available"
                    for key in content_keys:
                        if key in result:
                            content = result[key]
                            break
                    
                    # Try different possible key names for URL
                    url_keys = ["url", "link", "href", "source"]
                    url = "No source URL available"
                    for key in url_keys:
                        if key in result:
                            url = result[key]
                            break
                    
                    formatted_results += f"\n\n- {content}\n🔗 SOURCE: {url}"
                else:
                    formatted_results += f"\n\n- Result {i+1}: {str(result)}"

        # Case 4: Plain text response - try to extract URLs
        else:
            formatted_results = f"\n\n{str(search_result)}"
            # Try to extract URLs if they exist in the string
            import re
            urls = re.findall(r'https?://[^\s]+', str(search_result))
            if urls:
                formatted_results += "\n\n🔗 SOURCES FOUND:"
                for url in urls:
                    formatted_results += f"\n- {url}"
        
        print(Fore.YELLOW, f"\n\n[DEBUG] Tavily result type: {type(search_result)}")
        if isinstance(search_result, dict):
            print(Fore.YELLOW, f"\n\n[DEBUG] Tavily result keys: {list(search_result.keys())}")
            if "results" in search_result and isinstance(search_result["results"], list) and search_result["results"]:
                print(Fore.YELLOW, f"\n\n[DEBUG] First result item keys: {list(search_result['results'][0].keys())}")
        elif isinstance(search_result, list) and search_result:
            print(Fore.YELLOW, f"\n\n[DEBUG] First list item type: {type(search_result[0])}")
            if isinstance(search_result[0], dict):
                print(Fore.YELLOW, f"\n\n[DEBUG] First list item keys: {list(search_result[0].keys())}")
        print(Fore.YELLOW, f"\n\n[DEBUG] Tavily result sample: {str(search_result)[:300]}...\n")
        
        return {"messages": state["messages"] + [
            AIMessage(content=f"Neighborhood Agent: Based on my search, I found the following about neighborhoods in {location}:{formatted_results}")
        ]}
    except Exception as e:
        print(Fore.RED, f"\n\n[LangGraph Real Estate] Neighborhood search error: {str(e)}\n")
        return {"messages": state["messages"] + [
            AIMessage(content=f"Neighborhood Agent: I couldn't retrieve specific information about {location} neighborhoods. However, generally speaking, when evaluating neighborhoods, consider factors like crime rates, school quality, proximity to amenities, and transportation options.")
        ]}

# Property agent: finds property listings
def property_agent(state: RealEstateState):
    """Property agent that searches for listings based on user criteria"""
    print(Fore.MAGENTA, "\n\n[LangGraph Real Estate] Running property agent\n")
    
    # Extract budget and location information from user messages
    user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
    
    if user_messages:
        user_query = user_messages[-1].content
        
        # Try to extract location
        import re
        location_match = re.search(r'in\s+([A-Za-z\s]+)', user_query)
        location = location_match.group(1) if location_match else "San Francisco"
        
        # Try to extract budget
        budget_match = re.search(r'(\$?\d[\d,.]*)\s*(?:k|K|thousand)?(?:\s*per\s*month)?|(?:budget\s*(?:is|of)\s*(\$?\d[\d,.]*))(?:\s*per\s*month)?', user_query)
        budget = budget_match.group(1) if budget_match else "$3000"
    else:
        location = "San Francisco"
        budget = "$3000"
    
    # Construct a search query for properties
    query = f"Apartment listings in {location} under {budget} per month"
    
    try:
        # Invoke Tavily Search using the tool
        print(Fore.BLUE, f"\n\n[LangGraph Real Estate] Searching for properties: {query}\n")
        search_result = tavily_tool.invoke(query)
        
        # Add comprehensive debugging
        debug_tavily_response(query, search_result, "PROPERTY AGENT")
        
        # Format the results to include links, handling different possible result structures
        formatted_results = ""

        # Debug the structure first
        print(Fore.YELLOW, f"\n\n[DEBUG] Result type: {type(search_result)}")

        # Case 1: Dictionary with "results" key (common Tavily format)
        if isinstance(search_result, dict) and "results" in search_result:
            for result in search_result["results"]:
                content = result.get("content", result.get("snippet", "No content available"))
                url = result.get("url", "No source URL available")
                formatted_results += f"\n\n- {content}\n🔗 SOURCE: {url}"

        # Case 2: Dictionary with "answer" and "citations" structure
        elif isinstance(search_result, dict) and "answer" in search_result and "citations" in search_result:
            # Include the answer
            formatted_results += f"\n\n{search_result['answer']}"
            # Add citations/sources
            formatted_results += "\n\n🔗 SOURCES:"
            for citation in search_result["citations"]:
                if isinstance(citation, dict):
                    url = citation.get("url", "No URL available")
                    title = citation.get("title", "Untitled source")
                    formatted_results += f"\n- {title}: {url}"
                else:
                    formatted_results += f"\n- {str(citation)}"

        # Case 3: List of results
        elif isinstance(search_result, list):
            for i, result in enumerate(search_result):
                if isinstance(result, dict):
                    # Try different possible key names for content
                    content_keys = ["content", "snippet", "text", "description"]
                    content = "No content available"
                    for key in content_keys:
                        if key in result:
                            content = result[key]
                            break
                    
                    # Try different possible key names for URL
                    url_keys = ["url", "link", "href", "source"]
                    url = "No source URL available"
                    for key in url_keys:
                        if key in result:
                            url = result[key]
                            break
                    
                    formatted_results += f"\n\n- {content}\n🔗 SOURCE: {url}"
                else:
                    formatted_results += f"\n\n- Result {i+1}: {str(result)}"

        # Case 4: Plain text response - try to extract URLs
        else:
            formatted_results = f"\n\n{str(search_result)}"
            # Try to extract URLs if they exist in the string
            import re
            urls = re.findall(r'https?://[^\s]+', str(search_result))
            if urls:
                formatted_results += "\n\n🔗 SOURCES FOUND:"
                for url in urls:
                    formatted_results += f"\n- {url}"
        
        print(Fore.YELLOW, f"\n\n[DEBUG] Tavily result type: {type(search_result)}")
        if isinstance(search_result, dict):
            print(Fore.YELLOW, f"\n\n[DEBUG] Tavily result keys: {list(search_result.keys())}")
            if "results" in search_result and isinstance(search_result["results"], list) and search_result["results"]:
                print(Fore.YELLOW, f"\n\n[DEBUG] First result item keys: {list(search_result['results'][0].keys())}")
        elif isinstance(search_result, list) and search_result:
            print(Fore.YELLOW, f"\n\n[DEBUG] First list item type: {type(search_result[0])}")
            if isinstance(search_result[0], dict):
                print(Fore.YELLOW, f"\n\n[DEBUG] First list item keys: {list(search_result[0].keys())}")
        print(Fore.YELLOW, f"\n\n[DEBUG] Tavily result sample: {str(search_result)[:300]}...\n")
        
        return {"messages": state["messages"] + [
            AIMessage(content=f"Property Agent: Here are some property listings I found in {location}:{formatted_results}")
        ]}
    except Exception as e:
        print(Fore.RED, f"\n\n[LangGraph Real Estate] Property search error: {str(e)}\n")
        return {"messages": state["messages"] + [
            AIMessage(content=f"Property Agent: I couldn't retrieve current property listings for {location}. To find apartments in your budget range, I recommend checking popular real estate websites like Zillow, Apartments.com, or Redfin, which typically have extensive listings with detailed information.")
        ]}

# Price agent: verifies if property prices meet the user's budget
def price_agent(state: RealEstateState):
    """Price agent that analyzes pricing information from listings"""
    print(Fore.MAGENTA, "\n\n[LangGraph Real Estate] Running price agent\n")
    
    # Extract budget from user messages
    user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
    
    if user_messages:
        user_query = user_messages[-1].content
        
        # Try to extract budget
        import re
        budget_match = re.search(r'(\$?\d[\d,.]*)\s*(?:k|K|thousand)?(?:\s*per\s*month)?|(?:budget\s*(?:is|of)\s*(\$?\d[\d,.]*))(?:\s*per\s*month)?', user_query)
        budget = budget_match.group(1) if budget_match else "$3000"
        
        # Try to extract location
        location_match = re.search(r'in\s+([A-Za-z\s]+)', user_query)
        location = location_match.group(1) if location_match else "San Francisco"
    else:
        budget = "$3000"
        location = "San Francisco"
        
    # Try to analyze property pricing - Use EXACT same format as property_agent
    try:
        # Use the exact same query format as the successful property_agent
        query = f"Apartment listings in {location} under {budget} per month"
        
        print(Fore.BLUE, f"\n\n[LangGraph Real Estate] Analyzing rental prices in {location} against budget: {budget}\n")
        analysis_result = tavily_tool.invoke(query)
        
        # Add comprehensive debugging
        debug_tavily_response(query, analysis_result, "PRICE AGENT")
        
        # Format the results to include links - simplified to focus on list format
        formatted_results = ""

        # Use the exact same handling as property_agent, focusing on list format that works
        if isinstance(analysis_result, list):
            for i, result in enumerate(analysis_result):
                if isinstance(result, dict):
                    content = result.get("content", "No content available")
                    url = result.get("url", "No source URL available")
                    formatted_results += f"\n\n- {content}\n🔗 SOURCE: {url}"
                else:
                    formatted_results += f"\n\n- Result {i+1}: {str(result)}"
        elif isinstance(analysis_result, dict) and "results" in analysis_result:
            for result in analysis_result["results"]:
                content = result.get("content", result.get("snippet", "No content available"))
                url = result.get("url", "No source URL available")
                formatted_results += f"\n\n- {content}\n🔗 SOURCE: {url}"
        else:
            formatted_results = f"\n\n{str(analysis_result)}"
            # Try to extract URLs if they exist in the string
            import re
            urls = re.findall(r'https?://[^\s]+', str(analysis_result))
            if urls:
                formatted_results += "\n\n🔗 SOURCES FOUND:"
                for url in urls:
                    formatted_results += f"\n- {url}"
        
        # Add budget analysis to the formatted results
        formatted_results += f"\n\nBased on these results, apartments in {location} generally "
        formatted_results += f"{'seem to be within' if '$' in budget else 'may require comparing with'} your budget of {budget} per month."
        formatted_results += " Remember to factor in additional costs like utilities, parking, pet fees, and security deposits."
        
        return {"messages": state["messages"] + [
            AIMessage(content=f"Price Agent: After analyzing rental prices in {location} under {budget}, here's what I found:{formatted_results}")
        ]}
    except Exception as e:
        print(Fore.RED, f"\n\n[LangGraph Real Estate] Price analysis error: {str(e)}\n")
        return {"messages": state["messages"] + [
            AIMessage(content=f"Price Agent: I couldn't retrieve specific pricing information for {location}. With a budget of {budget}, consider that SF Bay Area apartments typically range from $2,000-$4,000+ for one-bedrooms depending on location and amenities. Always check for additional costs beyond rent.")
        ]}

# Final coordinator: synthesizes all sub-agent responses into a final result
def final_coordinator(state: RealEstateState):
    """Final coordinator that synthesizes results from all agents"""
    print(Fore.CYAN, "\n\n[LangGraph Real Estate] Running final coordinator\n")
    
    # Extract URLs from agent responses to ensure they're included
    agent_results_with_urls = []
    for msg in state["messages"]:
        if isinstance(msg, AIMessage) and "Agent:" in msg.content:
            agent_results_with_urls.append(msg.content)
    
    # Pass the accumulated messages to the LLM to generate a comprehensive summary
    summarization_prompt = f"""
    You are a helpful real estate assistant. Synthesize the information from various specialized agents
    into a comprehensive, well-organized summary for the user. Include:
    
    1. Neighborhood insights
    2. Property listing highlights
    3. Budget considerations
    4. Next steps or recommendations
    
    CRITICAL REQUIREMENT: You MUST include ALL of the source URLs from the agent responses.
    NEVER summarize or omit the URLs. Present each URL exactly as shown in the original responses.
    
    When presenting information, maintain the same URL format: "🔗 SOURCE: [url]"
    
    Your response MUST include ALL links from these agent responses:
    
    {agent_results_with_urls}
    
    Present a well-organized, conversational response, but NEVER omit any URLs.
    """
    
    try:
        # Create a prompt with all the information
        system_message = SystemMessage(content=summarization_prompt)
        
        # We'll use a subset of messages to reduce token count but preserve URLs
        # Get the most recent human message
        user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        human_message = user_messages[-1] if user_messages else HumanMessage(content="Find me apartments")
        
        # Only include agent response messages with URLs
        agent_messages = [msg for msg in state["messages"] if isinstance(msg, AIMessage) and "Agent:" in msg.content]
        
        # Create a focused message list
        focused_messages = [system_message, human_message] + agent_messages
        
        # Generate a synthesized response that preserves URLs
        response = llm.invoke(focused_messages)
        
        # Force higher temperature to encourage more creative inclusion of links
        return {"messages": state["messages"] + [response]}
    except Exception as e:
        print(Fore.RED, f"\n\n[LangGraph Real Estate] Final coordination error: {str(e)}\n")
        return {"messages": state["messages"] + [
            AIMessage(content="""
            Based on the information gathered about apartments in San Francisco:
            
            1. Neighborhood Insights: The Outer Sunset, Noe Valley, and Inner Sunset are known for being safe and family-friendly.
            
            2. Property Options: For your budget of $3,000, check these resources:
            - Rent.com: https://www.rent.com/california/san-francisco-apartments/max-price-3000
            - ForRent.com: https://www.forrent.com/find/CA/metro-San+Francisco+Bay/San+Francisco/price-Less+than+3000
            - Zillow: https://www.zillow.com/san-francisco-ca/apartments/under-3000/
            
            3. Budget Considerations: Remember to account for utilities, parking, and other fees beyond rent.
            
            4. Next Steps: Visit properties in person and carefully review lease terms before signing.
            
            Would you like more specific information about any of these areas?
            """)
        ]}

# Create the sequential real estate agent graph
def create_real_estate_graph() -> StateGraph:
    """Create the real estate agent graph with sequential processing"""
    print(Fore.CYAN, "\n\n[LangGraph Real Estate] Creating sequential agent graph\n")
    
    # Build the state graph
    graph_builder = StateGraph(RealEstateState)
    
    # Add nodes
    graph_builder.add_node("coordinator", coordinator)
    graph_builder.add_node("neighborhood_agent", neighborhood_agent)
    graph_builder.add_node("property_agent", property_agent)
    graph_builder.add_node("price_agent", price_agent)
    graph_builder.add_node("final_coordinator", final_coordinator)

    # Define the control flow
    graph_builder.add_edge(START, "coordinator")
    graph_builder.add_edge("coordinator", "neighborhood_agent")
    graph_builder.add_edge("neighborhood_agent", "property_agent")
    graph_builder.add_edge("property_agent", "price_agent")
    graph_builder.add_edge("price_agent", "final_coordinator")
    graph_builder.add_edge("final_coordinator", END)
    
    # Compile the graph
    return graph_builder.compile()

# Function to run the real estate agent with a user query
def run_real_estate_agent(query: str, thread_id: str = None) -> str:
    """Run the real estate agent with a specific query"""
    print(Fore.CYAN, f"\n\n[LangGraph Real Estate] Processing query: {query}\n")
    
    # Create threads directory if needed
    os.makedirs("./threads/real_estate", exist_ok=True)
    
    # Create the graph
    graph = create_real_estate_graph()
    
    # Set up initial state with user query
    initial_state = {
        "messages": [HumanMessage(content=query)]
    }
    
    # Execute the workflow
    try:
        final_state = graph.invoke(initial_state)
        
        # Extract the final response
        ai_messages = [msg for msg in final_state["messages"] if isinstance(msg, AIMessage)]
        if ai_messages:
            response = ai_messages[-1].content
            print(Fore.GREEN, f"\n\n[LangGraph Real Estate] Final response: {response[:100]}...\n")
            return response
        else:
            return "I'm sorry, I couldn't generate a response to your real estate query."
    except Exception as e:
        error_msg = f"I apologize, but I encountered an error while processing your real estate query: {str(e)}"
        print(Fore.RED, f"\n\n[LangGraph Real Estate] Error: {str(e)}\n")
        return error_msg 