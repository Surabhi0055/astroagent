from dotenv import load_dotenv
import os
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from typing import TypedDict, List

load_dotenv()

# State schema
class AgentState(TypedDict):
    messages: List[str]

# LLM setup
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

# Reasoning node
def reasoning_node(state: AgentState):
    user_message = state["messages"][-1]
    response = llm.invoke(user_message)
    return {"messages": state["messages"] + [response.content]}

# Build graph
graph = StateGraph(AgentState)
graph.add_node("reasoning", reasoning_node)
graph.set_entry_point("reasoning")
graph.add_edge("reasoning", END)
app = graph.compile()

# Test it
if __name__ == "__main__":
    result = app.invoke({
        "messages": ["Hello! I am an astrology assistant. Say hi back!"]
    })
    print("Agent response:", result["messages"][-1])