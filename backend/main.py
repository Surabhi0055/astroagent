from dotenv import load_dotenv
import os
import json
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import TypedDict, List, Annotated, Literal
import operator

load_dotenv()

# ── Tools ──────────────────────────────────────────────────────────────────

@tool
def geocode_place(place_name: str) -> str:
    """Convert a place name to latitude, longitude and timezone."""
    from tools.geocode import geocode_place as _geocode
    result = _geocode(place_name)
    return json.dumps(result)

@tool
def compute_birth_chart(date: str, time: str, latitude: float, longitude: float, timezone: str) -> str:
    """Compute planetary positions for a birth chart. Date format: YYYY-MM-DD, Time format: HH:MM"""
    from tools.birth_chart import compute_birth_chart as _chart
    result = _chart(date, time, latitude, longitude, timezone)
    return json.dumps(result)

@tool
def get_daily_transits(date: str, natal_chart: str) -> str:
    """Get current planetary transits and compare to natal chart. natal_chart should be JSON string."""
    from tools.transits import get_daily_transits as _transits
    natal = json.loads(natal_chart)
    result = _transits(date, natal)
    return json.dumps(result)

@tool
def knowledge_lookup(query: str) -> str:
    """Search the Aradhana spiritual database for astrology interpretations. Use this to explain planet placements."""
    from tools.knowledge import lookup_astrology_meaning as _lookup
    return _lookup(query)

tools = [geocode_place, compute_birth_chart, get_daily_transits, knowledge_lookup]

# ── LLM ────────────────────────────────────────────────────────────────────

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
).bind_tools(tools)

# ── State ──────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[List, operator.add]
    intent: str

# ── System Prompt ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are AstroAgent, a warm, empathetic, and spiritual guide for Aradhana.
You act as a thoughtful mirror, helping users reflect on their journey using astrology.

Important rules:
- Always be conversational, compassionate, and calm.
- Never give generic horoscope traits; instead, use the knowledge_lookup tool to find profound spiritual meanings for planet placements.
- ALWAYS use tools to get real planetary data — NEVER invent positions.
- NEVER present readings as medical, legal, or financial advice. If a user asks for certainty in these areas, gently guide them back to spiritual reflection.
- If birth details are missing, kindly ask for them.

When a user shares birth details, always:
1. Geocode their birth place.
2. Compute their birth chart.
3. Look up the meanings using knowledge_lookup.
4. Interpret the results warmly.
"""

# ── Router (Intent Classification) ─────────────────────────────────────────

class Intent(BaseModel):
    intent: Literal["chart_request", "daily_horoscope", "free_form_question", "off_topic"] = Field(
        description="Classify the user intent into one of the available categories."
    )

# Using temperature 0 for more deterministic routing
router_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
).with_structured_output(Intent)

def router_node(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1] if messages else None
    
    if last_message and isinstance(last_message, HumanMessage):
        try:
            classification = router_llm.invoke(
                f"Classify this user message: {last_message.content}"
            )
            return {"intent": classification.intent}
        except Exception:
            return {"intent": "free_form_question"}
            
    return {"intent": "free_form_question"}

# ── Nodes ──────────────────────────────────────────────────────────────────

def reasoning_node(state: AgentState):
    messages = state["messages"]
    
    intent = state.get("intent", "free_form_question")
    
    # Prepend system prompt if not present
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        
    # If the intent is off_topic, add a temporary system message to guide behavior
    if intent == "off_topic":
        messages = messages + [SystemMessage(content="The user has asked an off-topic question. Politely refuse to answer and guide them back to astrology or spiritual reflection.")]
        
    response = llm.invoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END

# ── Graph ──────────────────────────────────────────────────────────────────

tool_node = ToolNode(tools)

graph = StateGraph(AgentState)
graph.add_node("router", router_node)
graph.add_node("reasoning", reasoning_node)
graph.add_node("tools", tool_node)

graph.set_entry_point("router")
graph.add_edge("router", "reasoning")
graph.add_conditional_edges("reasoning", should_continue)
graph.add_edge("tools", "reasoning")
app = graph.compile()