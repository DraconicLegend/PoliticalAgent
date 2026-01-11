
import os
import json
from typing import TypedDict, Annotated, Sequence, List
from operator import add as add_messages

from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_ollama import ChatOllama

from langgraph.graph import StateGraph, END

load_dotenv()

# --- CONFIGURATION ---
llm = ChatOllama(
    model="llama3.1", 
    temperature=0  # Less stochastic to prevent hallucination
)

# Initialize Tavily Tool
tavily_tool = TavilySearchResults(max_results=5)

# --- STATE DEFINITION ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    query: str
    context: List[str]      # Context for search results
    plan: List[str]         # Search queries
    draft: str              # Current draft response
    critique: str           # Feedback from Neutralizer or FactChecker
    revision_count: int     # To prevent infinite loops
    is_political: bool      # Gatekeeper flag
    is_valid: bool          # Final quality gate

# --- NODES ---

def router_node(state: AgentState) -> AgentState:
    """
    Gatekeeper: Determine if the query is political, its complexity, and if it is within bounds.
    """
    messages = state['messages']
    last_message = messages[-1].content
    
    system_prompt = (
        "You are the Lead Dispatcher for a Political Intelligence Agent. Your task is to analyze the user's intent.\n"
        "Categorize: Is this a factual political query, a request for policy analysis, or non-political?\n"
        "Boundary Check: If the request is non-political (e.g., weather, homework), flag it for the 'Redirect Node'.\n"
        "Complexity: If political, identify the core 'tension' in the topic (e.g., 'Economic Impact vs. Social Equity').\n"
        "Constraint: Do not answer the question. Only output a JSON object containing keys: 'category', 'is_political' (boolean), and 'primary_entities'."
    )
    
    # We ask the LLM to classify.
    # Note: Llama 3.1 is good at JSON if prompted.
    try:
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=last_message)])
        # Basic parsing attempt, robust agents might use JsonOutputParser
        content = response.content.replace('```json', '').replace('```', '').strip()
        data = json.loads(content)
        is_political = data.get('is_political', False)
        print(f"Router Decision: Political={is_political}")
    except Exception as e:
        print(f"Router Parse Error: {e}. Defaulting to political for safety/testing.")
        is_political = True

    return {"is_political": is_political, "query": last_message}

def planner_node(state: AgentState) -> AgentState:
    """
    Strategist: Break a complex topic into searchable sub-tasks.
    """
    query = state['query']
    
    system_prompt = (
        "You are a Research Strategist. Your goal is to dismantle a political query into a multi-perspective search plan.\n"
        "Decompose: Identify the mainstream 'pro' arguments, the mainstream 'con' arguments, and the legal/historical context.\n"
        "Diversity of Search: Generate 3-5 distinct search queries for the Tavily tool. "
        "Ensure at least one query is specifically phrased to find opposing viewpoints (e.g., 'critiques of [Policy X]').\n"
        "Constraint: Return ONLY a JSON list of strings, e.g., [\"query 1\", \"query 2\"]. "
        "Avoid partisan language in your search queries."
    )
    
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=query)])
    
    try:
        content = response.content.replace('```json', '').replace('```', '').strip()
        plan = json.loads(content)
        if not isinstance(plan, list): 
            # Fallback if LLM creates a dict or string
            plan = [query]
    except:
        plan = [query] # Fallback
        
    print(f"Planner created {len(plan)} search queries.")
    return {"plan": plan}

def researcher_node(state: AgentState) -> AgentState:
    """
    data Collector: Interface with Tavily API.
    """
    plan = state.get('plan', [])
    critique = state.get('critique', "")
    
    # If we are here because of a loop-back (critique exists), we might need to adjust search
    # For simplicity, we just execute the plan. Real advanced agents might refine the plan based on critique.
    
    print("Researcher executing search plan...")
    context_results = []
    
    # Execute searches
    for query in plan:
        try:
            results = tavily_tool.invoke(query)
            # Tavily returns a list of dictionaries usually
            if isinstance(results, list):
                for r in results:
                    content = r.get('content', '')
                    url = r.get('url', '')
                    context_results.append(f"Source ({url}): {content}")
            else:
                context_results.append(str(results))
        except Exception as e:
            print(f"Search failed for '{query}': {e}")

    # Deduplicate and basic evaluation could happen here
    state['context'] = context_results
    return {"context": context_results}

def synthesis_node(state: AgentState) -> AgentState:
    """
    Writer: Create initial draft using Perspective-Balance framework.
    """
    query = state['query']
    context = "\n\n".join(state.get('context', []))
    critique = state.get('critique', "")
    
    prompt_content = (
        f"Context provided below:\n{context}\n\n"
        f"User Question: {query}\n\n"
    )
    
    if critique:
         prompt_content += f"PREVIOUS FEEDBACK TO ADDRESS: {critique}\n"

    system_prompt = (
        "You are a Neutral Policy Analyst. Your goal is to synthesize search data into a balanced report.\n"
        "Structure: Start with a neutral overview, followed by 'Perspective A', then 'Perspective B', and conclude with 'Areas of Consensus/Uncertainty'.\n"
        "Attribution: Every claim must be tied to a search result.\n"
        "Constraint: Do not use 'Golden Mean' fallacies. Present the strongest version of each side’s argument fairly."
    )
    
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=prompt_content)])
    return {"draft": response.content, "revision_count": state.get("revision_count", 0) + 1}

def neutralizer_node(state: AgentState) -> AgentState:
    """
    Editor: Detect bias and 'emotional' language. Loop-Back node.
    """
    draft = state['draft']
    
    system_prompt = (
        "You are a Linguistic Auditor. You review drafts for hidden partisan bias.\n"
        "Adjective Check: Identify and remove loaded words (e.g., 'radical', 'common-sense', 'extreme').\n"
        "Balance Check: Does one perspective have more 'real estate' than the other?\n"
        "Output: If bias is detected, return 'BIAS: <specific instruction>'. If neutral, return 'NEUTRAL'."
    )
    
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=draft)])
    result = response.content.strip()
    
    if result.startswith("BIAS"):
        return {"critique": result, "is_valid": False}
    else:
        return {"critique": "None", "is_valid": True} # Tentatively valid, go to fact check

def fact_checker_node(state: AgentState) -> AgentState:
    """
    Validator: Prevent hallucinations. Loop-Back node.
    """
    draft = state['draft']
    context = "\n\n".join(state.get('context', []))
    
    system_prompt = (
        "You are a Forensic Fact-Checker. You have zero tolerance for hallucinations.\n"
        "Verification: Compare every fact in the draft against the search context provided below.\n"
        f"Context:\n{context}\n\n"
        "Draft to Check:\n" + draft + "\n\n"
        "Output: If a claim is unsupported, return 'HALLUCINATION: <claim>'. "
        "If verify, return 'VERIFIED'."
    )
    
    response = llm.invoke([SystemMessage(content=system_prompt)])
    result = response.content.strip()
    
    if "HALLUCINATION" in result:
        return {"critique": result, "is_valid": False}
    
    return {"is_valid": True}

def redirect_node(state: AgentState) -> AgentState:
    """Handles non-political queries politely."""
    return {"messages": [AIMessage(content="I am a specialized Political Intelligence Agent. I can only assist with political queries.")]}

# --- EDGES ---

def route_initial(state: AgentState):
    if state['is_political']:
        return "planner_node"
    return "redirect_node"

def route_neutrality(state: AgentState):
    if state.get('revision_count', 0) > 3:
        return END # Force exit to avoid loop
    
    if not state['is_valid']:
        # Bias detected, go back to synthesis
        return "synthesis_node"
    return "fact_checker_node"

def route_facts(state: AgentState):
    if state.get('revision_count', 0) > 4: # Give it one more chance
        return END
        
    if not state.get('is_valid', True):
        # Fact check failed, go back to researcher to get more info or synthesis?
        # Plan says: "If verify failed... back to Researcher"
        return "researcher_node"
    return END

# --- GRAPH ---

graph = StateGraph(AgentState)

graph.add_node("router_node", router_node)
graph.add_node("planner_node", planner_node)
graph.add_node("researcher_node", researcher_node)
graph.add_node("synthesis_node", synthesis_node)
graph.add_node("neutralizer_node", neutralizer_node)
graph.add_node("fact_checker_node", fact_checker_node)
graph.add_node("redirect_node", redirect_node)

graph.set_entry_point("router_node")

graph.add_conditional_edges("router_node", route_initial)
graph.add_edge("planner_node", "researcher_node")
graph.add_edge("researcher_node", "synthesis_node")
graph.add_edge("synthesis_node", "neutralizer_node")

graph.add_conditional_edges(
    "neutralizer_node",
    route_neutrality,
    {
        "synthesis_node": "synthesis_node",
        "fact_checker_node": "fact_checker_node",
        END: END
    }
)

graph.add_conditional_edges(
    "fact_checker_node",
    route_facts,
    {
        "researcher_node": "researcher_node",
        END: END
    }
)

graph.add_edge("redirect_node", END)

rag_agent = graph.compile()


# --- VISUALIZATION & RUN ---

try:
    png_bytes = rag_agent.get_graph().draw_mermaid_png()
    with open("agent_graph.png", "wb") as f:
        f.write(png_bytes)
    print("Graph saved to agent_graph.png")
except Exception as e:
    print(f"Graph visualization failed: {e}")

def running_agent():
    print("\n=== POLITICAL INTELLIGENCE AGENT ===")
    print("Type 'exit' to quit.")
    
    while True:
        try:
            user_input = input("\nQuery: ")
            if user_input.lower() in ['exit', 'quit']:
                break
                
            messages = [HumanMessage(content=user_input)]
            
            result = rag_agent.invoke({
                "messages": messages,
                "query": user_input,
                "context": [],
                "plan": [],
                "draft": "",
                "critique": "",
                "revision_count": 0,
                "is_political": False,
                "is_valid": True
            })
            
            print("\n=== FINAL RESPONSE ===")
            if result.get("draft"):
                print(result["draft"])
            elif result.get("messages"):
                # Handle redirect
                print(result["messages"][-1].content)
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    running_agent()