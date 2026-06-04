from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import json
import logging

from main import app as agent_app
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

app = FastAPI(title="AstroAgent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from typing import Optional, Dict, Any
from tools.svg_chart import generate_birth_chart_image

from typing import List

class ChatRequest(BaseModel):
    message: str
    mode: str = "western"  # "western" or "vedic"
    user_context: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, str]]] = None

class ChartImageRequest(BaseModel):
    planets: Dict[str, Any]
    houses: Dict[str, Any]
    ascendant: float
    midheaven: float
    name: str
    birth_info: str

async def generate_chat_stream(user_message: str, mode: str, user_context: Optional[Dict[str, Any]] = None, history: Optional[List[Dict[str, str]]] = None):
    # Inject user context directly into the first message or let the agent state handle it
    # For LangGraph, passing it via a system message at the start is effective
    messages = []
    if user_context:
        gender_str = f" Gender: {user_context.get('gender')}." if user_context.get('gender') else ""
        ctx_str = f"System Context: The user's name is {user_context.get('name', 'Seeker')}.{gender_str} Birth details: {user_context.get('date', '')} {user_context.get('time', '')} in {user_context.get('place', '')}."
        if user_context.get('computed_chart'):
            slim_chart = {
                k: v for k, v in user_context['computed_chart'].items()
                if k not in ['aspects', 'houses']
            }
            ctx_str += f"\n\n[CACHED SESSION STATE] Pre-computed Natal Chart:\n{json.dumps(slim_chart)}\n(Note: Do not call compute_birth_chart, the data is already provided above.)"
        messages.append(SystemMessage(content=ctx_str))
        
    if history:
        # Only keep the last 4 messages to prevent exceeding Groq TPM limits
        recent_history = history[-4:]
        for h in recent_history:
            if h.get("role") == "user":
                messages.append(HumanMessage(content=h.get("content", "")))
            elif h.get("role") == "agent":
                messages.append(AIMessage(content=h.get("content", "")))

    messages.append(HumanMessage(content=user_message))
    
    inputs = {
        "messages": messages,
        "mode": mode
    }
    import time
    from datetime import datetime
    
    tool_timings = {}

    try:
        async for event in agent_app.astream_events(inputs, version="v2"):
            kind = event["event"]
            run_id = event.get("run_id")
            
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
                    
            elif kind == "on_tool_start":
                tool_name = event["name"]
                tool_inputs = event["data"].get("input", {})
                started_at_str = datetime.now().strftime("%H:%M:%S")
                tool_timings[tool_name] = time.time()
                
                yield f"data: {json.dumps({'type': 'tool_start', 'tool': tool_name, 'inputs': tool_inputs, 'started_at': started_at_str})}\n\n"
                
            elif kind == "on_tool_end":
                tool_name = event["name"]
                tool_output = event["data"].get("output", "")
                if hasattr(tool_output, "content"):
                    tool_output = tool_output.content
                    
                duration_ms = 0
                if tool_name in tool_timings:
                    duration_ms = int((time.time() - tool_timings[tool_name]) * 1000)
                    
                completed_at_str = datetime.now().strftime("%H:%M:%S")
                    
                yield f"data: {json.dumps({'type': 'tool_end', 'tool': tool_name, 'output': str(tool_output), 'completed_at': completed_at_str, 'duration_ms': duration_ms})}\n\n"

        yield "data: [DONE]\n\n"
    except Exception as e:
        logging.error(f"Error in stream: {e}")
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    return StreamingResponse(
        generate_chat_stream(request.message, request.mode, request.user_context, request.history), 
        media_type="text/event-stream"
    )

@app.post("/api/chart/image")
async def generate_chart_image(request: ChartImageRequest):
    try:
        result = generate_birth_chart_image(
            request.planets,
            request.houses,
            request.ascendant,
            request.midheaven,
            request.name,
            request.birth_info
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
