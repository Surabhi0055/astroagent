from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import json
import logging

from main import app as agent_app
from langchain_core.messages import HumanMessage

app = FastAPI(title="AstroAgent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

async def generate_chat_stream(user_message: str):
    inputs = {
        "messages": [HumanMessage(content=user_message)]
    }
    
    try:
        async for event in agent_app.astream_events(inputs, version="v2"):
            kind = event["event"]
            
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
                    
            elif kind == "on_tool_start":
                tool_name = event["name"]
                tool_inputs = event["data"].get("input", {})
                yield f"data: {json.dumps({'type': 'tool_start', 'tool': tool_name, 'inputs': tool_inputs})}\n\n"
                
            elif kind == "on_tool_end":
                tool_name = event["name"]
                yield f"data: {json.dumps({'type': 'tool_end', 'tool': tool_name})}\n\n"

        yield "data: [DONE]\n\n"
    except Exception as e:
        logging.error(f"Error in stream: {e}")
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    return StreamingResponse(
        generate_chat_stream(request.message), 
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
