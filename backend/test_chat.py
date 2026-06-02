import requests
import json
import sys

def chat_with_agent(message: str):
    print(f"You: {message}")
    print("AstroAgent: ", end="", flush=True)
    
    response = requests.post(
        "http://localhost:8080/api/chat",
        json={"message": message},
        stream=True
    )
    
    if response.status_code != 200:
        print(f"\nError: Could not connect to API (Status {response.status_code})")
        return

    for line in response.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith("data: ") and decoded != "data: [DONE]":
                try:
                    data = json.loads(decoded[6:])
                    if data["type"] == "token":
                        print(data["content"], end="", flush=True)
                    elif data["type"] == "tool_start":
                        print(f"\n[Tool Started: {data['tool']}] ", end="", flush=True)
                    elif data["type"] == "tool_end":
                        print(f"[Tool Finished: {data['tool']}]\n", end="", flush=True)
                except json.JSONDecodeError:
                    pass
    print("\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
    else:
        message = "Hi! I was born on June 15, 1995 at 10:30 AM in Mumbai. Can you tell me what my Sun sign means?"
        
    chat_with_agent(message)
