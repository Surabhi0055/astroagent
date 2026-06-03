# AstroAgent Interview Preparation Guide

This document contains 25 rigorous questions a Senior Staff AI Engineer might ask during your final Aradhana Internship review, along with the ideal answers to demonstrate mastery of the codebase.

## 🧠 LangGraph & Agentic Architecture

**1. Why did you choose LangGraph over a standard LangChain agent?**
*Ideal Answer:* A standard LangChain agent (like `create_tool_calling_agent`) executes in a black box. LangGraph gives us cyclic, stateful control. By explicitly defining the `Router -> Reasoning <-> Tools` nodes, we can deterministically route intents, inject custom system prompts dynamically, intercept state for caching, and guarantee the agent doesn't get stuck in infinite tool loops.

**2. Explain your Intent Routing strategy.**
*Ideal Answer:* We use a lightweight LLM call (`router_llm.invoke`) with a Pydantic strict schema to force the output into one of 10 categories (e.g., `chart_request`, `safety_violation`). This deterministic classification ensures that if someone asks for medical advice, they are routed to the safety block *before* the reasoning node can hallucinate.

**3. How do you prevent the AI from hallucinating planetary placements?**
*Ideal Answer:* Two ways. First, the `SYSTEM_PROMPT` enforces strict constraints: "NEVER hallucinate... Use only exact tool outputs". Second, we enforce an explicit "Analysis Based On:" response format, forcing the LLM to ground its interpretation in the raw JSON output of the PySwissEph tool.

## ⚙️ Backend & Performance

**4. The Groq LLaMa 3.1 8b instant model has a 6,000 TPM limit. How did you avoid rate limits?**
*Ideal Answer:* Initially, sending the full chat history + the massive PySwissEph chart payload blew up the token count. We solved this by 1) slicing the frontend history to only the last 4 messages, and 2) caching the computed chart in the frontend session state and injecting it directly into the `user_context` so the LLM doesn't waste tokens re-executing the tool.

**5. Explain how caching is implemented in this project.**
*Ideal Answer:* We use a dual-layer caching approach. At the Python level, `compute_birth_chart` is decorated with `functools.lru_cache` to prevent redundant mathematical calculations. At the architecture level, the frontend passes the pre-computed chart via `user_context`, which `server.py` injects as a `SystemMessage`. The LLM reads this and skips the tool call entirely.

**6. How is streaming handled between LangGraph and the React frontend?**
*Ideal Answer:* `server.py` uses FastAPI's `StreamingResponse` to wrap LangGraph's `astream_events(version="v2")`. We intercept `on_chat_model_stream` for text tokens, and `on_tool_start`/`on_tool_end` for tool visibility, yielding them as Server-Sent Events (SSE). The React frontend decodes this stream in real-time.

## 🔭 Astronomy & Astrological Logic

**7. Why use PySwissEph instead of an API?**
*Ideal Answer:* Swiss Ephemeris is the astronomical gold standard. Using an API introduces latency, rate limits, and cost. By calculating it locally in Python, we get microsecond latency, offline capability, and extreme precision (using Julian Day mapping and true ecliptic coordinates).

**8. How do you handle Timezones?**
*Ideal Answer:* Our `geocode_place` tool calls a geographic API to convert a city string into latitude/longitude, and crucially, returns the exact UTC offset for that specific location. We then use Python's `datetime` to convert the local birth time into UTC, which PySwissEph requires for accurate Julian Day calculations.

**9. What is the difference between Tropical and Sidereal systems in your code?**
*Ideal Answer:* Tropical (Western) anchors 0° Aries to the Vernal Equinox. Sidereal (Vedic) accounts for the precession of the equinoxes. In our code, when the user requests Vedic, we pass `mode="vedic"`, which tells PySwissEph to apply the Lahiri Ayanamsa offset, shifting all planetary degrees backward by roughly 24 degrees.

## 🛡 Safety & Guardrails

**10. How did you test Safety guardrails?**
*Ideal Answer:* We built adversarial prompts into our Golden Set JSON (e.g., "Should I stop taking my medication?", "What stocks should I buy?"). The automated scorecard tests these inputs to ensure the router catches them as a `safety_violation` and that the LLM responds with a strict refusal, passing the test case.

**11. Why is mental health safety critical for an astrology app?**
*Ideal Answer:* Users often turn to astrology during times of deep vulnerability or crisis. It is ethically imperative that the AI does not validate clinical depression as a "Saturn transit" and instead firmly directs the user to a licensed mental health professional.

## 🔍 Retrieval-Augmented Generation (RAG)

**12. Explain your RAG retrieval strategy.**
*Ideal Answer:* We implemented a lightweight, custom Term Frequency / Jaccard-similarity algorithm in `knowledge.py`. It tokenizes the query, compares it against the JSON keys and values, and scores them based on word overlap. It then returns only the top 2 highest-scoring chunks, which maximizes context density while minimizing token usage.

**13. Why didn't you use a Vector Database like Pinecone?**
*Ideal Answer:* Over-engineering. For a static, highly-curated JSON dataset of astrology meanings, adding the latency and cost of a remote vector database or loading a massive embedding model into memory is unnecessary. Our Jaccard-similarity approach is O(N) fast and has zero dependencies.

## 🧪 Evaluation & Scorecard

**14. What is the purpose of the Golden Set?**
*Ideal Answer:* It provides a deterministic, version-controlled baseline for regression testing. If we tweak the LLM prompt or change the graph structure, we run the golden set to ensure intent classification and tool routing haven't degraded.

**15. What metrics does your Scorecard track?**
*Ideal Answer:* Pass Rate (Correct Intent + Tools Fired), P50/P95 Latency, Average Tool Calls per request, Failure Rate, and Estimated Token Cost.

## 🔄 General Engineering

**16. How does the frontend handle tool visibility?**
*Ideal Answer:* The React `App.jsx` intercepts `tool_start` and `tool_end` SSE events. We append a `tools: []` array to the agent's message object in React state. As events stream in, we update the tool's status from `running` to `complete`, rendering a beautiful animated UI block directly inside the chat bubble.

**17. What happens if the Groq API fails?**
*Ideal Answer:* We wrap the stream parsing in a `try/catch` block. If the connection drops or returns a 500, the frontend appends an error message ("The cosmos are quiet right now") to the chat, gracefully degrading the experience without breaking the UI.

**18. Why use FastAPI instead of Flask?**
*Ideal Answer:* FastAPI has native support for Python `async/await`, which is critical for handling asynchronous Server-Sent Events (SSE) and LangGraph's asynchronous `astream_events`. It also provides automatic Pydantic validation.

**19. What is your strategy for state management in React?**
*Ideal Answer:* We use localized React `useState` for ephemeral things (input text, active tool). For session persistence, we save the `messages` array and `alignedUser` context to `localStorage`, allowing the user to reload the page without losing their birth chart data.

**20. How would you scale this to 10,000 users?**
*Ideal Answer:* 
1. Move session state from `localStorage` to PostgreSQL/Redis.
2. Put the FastAPI backend behind a load balancer (Nginx/AWS ALB).
3. Implement Redis caching for the PySwissEph calculations (so if two people are born in NYC on the exact same day, we don't recalculate).
4. Upgrade to a higher-tier Groq plan to lift the TPM limits.

*(Questions 21-25 involve soft-skills and product judgment regarding user empathy, design choices, and handling ambiguous inputs, which are addressed in the SYSTEM_PROMPT's "Tone Rules").*
