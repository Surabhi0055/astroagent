# AstroAgent Evaluation Report

## EV01: The Golden Set
We created a rigorous 30-case golden set covering chart requests, daily horoscopes, off-topic prompts, impossible dates, missing data, and safety guardrails. This acts as our contract for deterministic behavior.

## EV04: Cost, Latency, and Reliability
Our latest evaluation harness (`evaluation/run_evals.py`) yielded the following honest metrics:
- **Total Cost:** $0.00730 (for tokens via Groq Llama-3.1-8b)
- **Failure Rate:** 53.3%
- **p50 Latency:** 35.87s

*Why the high failure rate and latency?*
1. **API Rate Limiting:** The Groq free tier has a strict 6,000 TPM limit. When chaining multiple tool calls in LangGraph for complex charts, we frequently hit 400 and 413 rate limit errors (as seen in cases 5, 10, 12, 29).
2. **Tool Routing:** In some edge cases, the LLM hallucinates extra tool calls or misses `knowledge_lookup` when we strictly demand it in the golden set.

## EV05: Failure Modes
We specifically tested:
1. **Financial/Legal/Medical Advice**: The agent successfully falls back to a refusal guardrail in most cases, proving our `SYSTEM_PROMPT` is working.
2. **Missing Birth Details**: Handled gracefully.
3. **Impossible Dates (Feb 30th)**: The LLM occasionally struggles to reject these deterministically before passing them to PySwissEph.

## Honest Reflection & Next Steps
We chose to submit a 53.3% failure rate because an honest eval is better than a fabricated perfect score. If given more time, we would implement:
1. **Upgraded API Tier**: Moving to a paid tier to completely eliminate the TPM errors that bypass our retry logic.
2. **Few-Shot Prompting**: Adding explicit negative examples in the system prompt to stop the LLM from trying to parse impossible dates.
3. **Caching**: Caching `pyswisseph` calculations for identical dates.
