import json
import os
import time
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import app as agent_app

def run_eval(test_case):
    input_text = test_case["input"]
    expected_intent = test_case["expected_intent"]
    
    start_time = time.time()
    
    # Run the agent synchronously for evaluation
    inputs = {"messages": [("user", input_text)], "mode": "western"}
    
    # Track metrics
    actual_intent = None
    tools_called = []
    
    try:
        for event in agent_app.stream(inputs):
            if "router" in event:
                actual_intent = event["router"].get("intent")
            if "tools" in event:
                # event["tools"]["messages"] contains ToolMessages
                tools_called.extend([m.name for m in event["tools"]["messages"]])
    except Exception as e:
        print(f"Error on {input_text}: {e}")
        
    latency = time.time() - start_time
    
    # Evaluate
    passed_intent = actual_intent == expected_intent
    passed_tools = True
    for t in test_case.get("must_call_tools", []):
        if t not in tools_called:
            passed_tools = False
            
    passed = passed_intent and passed_tools
    
    # Token proxy based on response length + input length
    # This is a naive estimation for the scorecard
    token_usage = len(input_text) // 4 + sum(len(str(t)) for t in tools_called) // 4 + 200
    
    return {
        "passed": passed,
        "latency": latency,
        "tools_called": len(tools_called),
        "tokens": token_usage
    }

def main():
    script_dir = os.path.dirname(__file__)
    golden_set_path = os.path.join(script_dir, "golden_set_expanded.jsonl")
    
    test_cases = []
    with open(golden_set_path, "r") as f:
        for line in f:
            if line.strip():
                test_cases.append(json.loads(line))
                
    print(f"Running evaluation on {len(test_cases)} test cases...")
    
    results = []
    # Run sequentially to respect Groq rate limits (6000 TPM limit)
    # Using a 2 second sleep between requests to avoid rate limits during eval
    for i, tc in enumerate(test_cases):
        print(f"Running {i+1}/{len(test_cases)}...")
        results.append(run_eval(tc))
        time.sleep(2.5) # Prevent Groq TPM rate limits
        
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    latencies = sorted([r["latency"] for r in results])
    p50 = latencies[total // 2] if total else 0
    p95 = latencies[int(total * 0.95)] if total else 0
    avg_tools = sum(r["tools_called"] for r in results) / total if total else 0
    total_tokens = sum(r["tokens"] for r in results)
    
    pass_rate = (passed / total) * 100
    failure_rate = 100 - pass_rate
    est_cost = (total_tokens / 1000000) * 0.05 # roughly LLaMa 3.1 8b pricing
    
    md_output = f"""# AstroAgent Evaluation Results

| Metric | Value |
|--------|-------|
| **Pass Rate** | {pass_rate:.1f}% |
| **P50 Latency** | {p50:.2f}s |
| **P95 Latency** | {p95:.2f}s |
| **Avg Tool Calls** | {avg_tools:.1f} |
| **Failure Rate** | {failure_rate:.1f}% |
| **Total Tokens (Est)** | {total_tokens} |
| **Est Cost** | ${est_cost:.5f} |

## Summary
Evaluated {total} rigorous test cases from the expanded golden set covering Intent Classification, Tool Execution, Missing Data Handling, and Safety Guardrails (Medical, Financial, Legal, Mental Health).
"""
    
    output_path = os.path.join(script_dir, "evaluation_results.md")
    with open(output_path, "w") as f:
        f.write(md_output)
        
    print(f"Evaluation complete! Results written to {output_path}")
    print(md_output)

if __name__ == "__main__":
    main()
