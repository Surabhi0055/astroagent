import sys
import os
import json
import time
from tabulate import tabulate

# Add backend to path so we can import the agent
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from main import app as agent_app
from langchain_core.messages import HumanMessage

def run_evaluation():
    print("🔮 Starting AstroAgent Evaluation Harness...")
    golden_set_path = os.path.join(os.path.dirname(__file__), "golden_set.jsonl")
    
    cases = []
    with open(golden_set_path, "r") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))
                
    results = []
    total_latency = 0
    total_tokens = 0 # Rough estimate since stream doesn't easily expose this
    
    for idx, case in enumerate(cases):
        print(f"\nRunning Eval Case {idx + 1}/{len(cases)}...")
        input_text = case["input"]
        expected_intent = case["expected_intent"]
        must_call_tools = case.get("must_call_tools", [])
        
        start_time = time.time()
        
        # We will invoke synchronously for evaluation
        inputs = {"messages": [HumanMessage(content=input_text)]}
        try:
            # First, check the intent by running just the router node manually for testing
            # Or we can just run the full graph and check state
            final_state = agent_app.invoke(inputs)
            latency = time.time() - start_time
            total_latency += latency
            
            # Extract actual intent and tools called
            actual_intent = final_state.get("intent", "unknown")
            
            # Find tools called in the messages
            tools_called = []
            for msg in final_state["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tools_called.append(tool_call["name"])
            
            # Determine success
            intent_pass = actual_intent == expected_intent
            tools_pass = all(t in tools_called for t in must_call_tools)
            success = intent_pass and tools_pass
            
            results.append({
                "Test Case": f"Case {idx + 1}",
                "Intent Pass": "✅" if intent_pass else "❌",
                "Tools Pass": "✅" if tools_pass else "❌",
                "Latency (s)": round(latency, 2),
                "Status": "PASS" if success else "FAIL"
            })
            
        except Exception as e:
            results.append({
                "Test Case": f"Case {idx + 1}",
                "Intent Pass": "❌",
                "Tools Pass": "❌",
                "Latency (s)": round(time.time() - start_time, 2),
                "Status": f"FAIL ({str(e)[:20]})"
            })
            
    # Print Scorecard
    print("\n" + "="*50)
    print("📊 EVALUATION SCORECARD")
    print("="*50)
    print(tabulate(results, headers="keys", tablefmt="github"))
    
    passed = sum(1 for r in results if r["Status"] == "PASS")
    print(f"\nOverall Pass Rate: {passed}/{len(cases)} ({passed/len(cases)*100:.1f}%)")
    print(f"Average Latency: {total_latency/len(cases):.2f}s")
    
if __name__ == "__main__":
    run_evaluation()
