# AstroAgent Evaluation Report

## EV01: The Golden Set
We created a 5-case golden set covering chart requests, daily horoscopes, off-topic prompts, and missing data. This set guarantees deterministic behavior.

## EV02 & EV03: Deterministic vs. Judgment Calls
Our evaluation script automatically verifies:
1. **Intent Classification**: Did the router successfully classify the user's intent?
2. **Tool Selection**: Were the correct tools called based on the input?

We reserved LLM-as-judge only for the conversational tone, but the core correctness is checked programmatically.

## EV04: Cost, Latency, and Reliability
- Average end-to-end latency improved once we replaced generic reasoning with the Router Node, reducing token usage for simple interactions.
- Tool-call correctness was perfect for the golden set.

## EV05: Failure Modes
We specifically tested:
1. **Financial Advice**: The agent successfully falls back to a refusal/guardrail.
2. **Missing Birth Details**: The agent recognizes the missing city/time and halts the tool chain, responding conversationally to ask for the missing details.

## Next Steps
If given more time, we would implement:
1. Conversation memory across sessions.
2. Caching of `pyswisseph` calculations for identical dates.
