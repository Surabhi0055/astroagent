from dotenv import load_dotenv
import os
import json
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from typing import TypedDict, List, Annotated
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

tools = [geocode_place, compute_birth_chart, get_daily_transits]

# ── LLM ────────────────────────────────────────────────────────────────────

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
).bind_tools(tools)

# ── State ──────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[List, operator.add]

# ── System Prompt ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are AstroAgent, a warm and caring AI astrologer for Aradhana — a daily spiritual companion app.

Your role is to:
- Compute accurate birth charts using real planetary data
- Interpret planetary positions with warmth and spiritual insight
- Answer questions about daily transits and their meaning
- Guide users through their astrological journey with care

Important rules:
- Always use tools to get real planetary data — never invent positions
- Never present readings as medical, legal, or financial certainty
- If birth details are missing, kindly ask for them
- Respond with warmth, empathy, and spiritual wisdom
- Keep responses conversational and grounded

When a user shares birth details, always:
1. First geocode their birth place
2. Then compute their birth chart
3. Then interpret the results warmly
"""

# ── Nodes ──────────────────────────────────────────────────────────────────

def reasoning_node(state: AgentState):
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
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
graph.add_node("reasoning", reasoning_node)
graph.add_node("tools", tool_node)
graph.set_entry_point("reasoning")
graph.add_conditional_edges("reasoning", should_continue)
graph.add_edge("tools", "reasoning")
app = graph.compile()

# ── Test ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🔮 AstroAgent is live!\n")
    result = app.invoke({
        "messages": [
            HumanMessage(content="Hi! My name is Priya. I was born on June 15, 1995 at 10:30 AM in Mumbai. What does my birth chart say?")
        ]
    })
    for message in result["messages"]:
        if isinstance(message, AIMessage) and message.content:
            print("AstroAgent:", message.content)