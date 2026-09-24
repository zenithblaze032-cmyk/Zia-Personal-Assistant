# System Architecture

Zia is structured as a central listening loop (`Zia.py`) with a hybrid routing and multi-agent system.

## Directory Layout
```text
Zia.py          ← Main loop: audio capture, state machine
core/
  asr.py           ← ASR pipeline (Google Speech)
  brain.py         ← EffGen complexity router & prompt compression
  context.py       ← Context object passed to skills
  executor.py      ← AgentKthx (Nova) wrapper with safety limits and OS/Web tools
  llm.py           ← Hybrid LLM router (Cascades HuggingFace -> Groq -> Gemini -> OpenRouter -> Local Ollama)
  nlp.py           ← spaCy NLP Entity Extraction
  screen.py        ← Screen Capture and Grounding Vision Engine (HuggingFace Qwen-VL -> Gemini)
  state.py         ← Thread-safe global state machine
skills/
  apps.py, media.py, web.py, etc. ← Direct regex command handlers
```

## Routing Flow
1. **Audio -> Text**: Captured via Google Speech API.
2. **Deterministic Check**: Matches against regex patterns in `skills/`. If found, executed immediately (e.g. "volume up").
3. **Brain Routing (Fallback)**: If no match, `brain.route_complexity()` determines if the query is SIMPLE or MULTI_STEP.
4. **Hybrid LLM Execution**: For SIMPLE or conversational queries, `core/llm.py` attempts to fetch answers from cloud APIs. If all fail, it falls back to the local Ollama instance.
5. **AgentNova (MULTI_STEP)**: If complex, AgentNova iteratively uses tools (like web search) to complete the goal.
