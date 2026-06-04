import sys
import os
import json
import time
import statistics
from tabulate import tabulate

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
    latencies = []
    total_cost = 0.0
    total_tokens = 0
    total_failures = 0
    
    for idx, case in enumerate(cases):
        print(f"\nRunning Eval Case {idx + 1}/{len(cases)}...")
        input_text = case["input"]
        expected_intent = case["expected_intent"]
        must_call_tools = case.get("must_call_tools", [])
        expected_behavior = case.get("expected_behavior")
        
        start_time = time.time()
        
        inputs = {"messages": [HumanMessage(content=input_text)]}
        try:
            final_state = agent_app.invoke(inputs)
            latency = time.time() - start_time
            latencies.append(latency)
            
            actual_intent = final_state.get("intent", "unknown")
            
            tools_called = []
            input_tokens = 0
            output_tokens = 0
            
            for msg in final_state["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tools_called.append(tool_call["name"])
                if hasattr(msg, "response_metadata") and msg.response_metadata:
                    usage = msg.response_metadata.get("token_usage", {})
                    if usage:
                        input_tokens += usage.get("prompt_tokens", 0)
                        output_tokens += usage.get("completion_tokens", 0)
            
            # Groq Llama-3.1-8b approximate pricing
            case_cost = (input_tokens / 1_000_000 * 0.05) + (output_tokens / 1_000_000 * 0.08)
            total_cost += case_cost
            total_tokens += (input_tokens + output_tokens)
            
            # Checks
            intent_pass = actual_intent == expected_intent
            tools_pass = all(t in tools_called for t in must_call_tools)
            
            success = intent_pass and tools_pass
            if not success:
                total_failures += 1
            
            results.append({
                "ID": f"{idx + 1}",
                "Intent Pass": "✅" if intent_pass else "❌",
                "Tools Pass": "✅" if tools_pass else "❌",
                "Tools Count": len(tools_called),
                "Tokens": input_tokens + output_tokens,
                "Latency (s)": f"{latency:.2f}",
                "Status": "PASS" if success else "FAIL"
            })
            
        except Exception as e:
            total_failures += 1
            results.append({
                "ID": f"{idx + 1}",
                "Intent Pass": "❌",
                "Tools Pass": "❌",
                "Tools Count": 0,
                "Tokens": 0,
                "Latency (s)": f"{(time.time() - start_time):.2f}",
                "Status": f"FAIL ({str(e)[:15]})"
            })
            
    # Calculate stats
    p50_latency = statistics.median(latencies) if latencies else 0
    p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies) if latencies else 0
    failure_rate = (total_failures / len(cases)) * 100
    
    # Save to MD
    md_content = f"# AstroAgent Evaluation Scorecard\n\n"
    md_content += f"**Total Runs:** {len(cases)}\n"
    md_content += f"**Failure Rate:** {failure_rate:.1f}%\n"
    md_content += f"**Total Cost:** ${total_cost:.5f}\n"
    md_content += f"**Total Tokens:** {total_tokens}\n"
    md_content += f"**p50 Latency:** {p50_latency:.2f}s\n"
    md_content += f"**p95 Latency:** {p95_latency:.2f}s\n\n"
    
    md_content += tabulate(results, headers="keys", tablefmt="github")
    
    out_path = os.path.join(os.path.dirname(__file__), "evaluation_results.md")
    with open(out_path, "w") as f:
        f.write(md_content)
        
    print("\n" + "="*50)
    print("📊 EVALUATION COMPLETE")
    print(f"Results saved to {out_path}")
    print(f"Failure Rate: {failure_rate:.1f}%")
    print(f"p50 Latency: {p50_latency:.2f}s")
    print(f"Total Cost: ${total_cost:.5f}")
    print("="*50)

if __name__ == "__main__":
    run_evaluation()
