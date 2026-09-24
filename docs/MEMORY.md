# Project Context — Zia

Quick-reference memory for anyone working on this codebase.

## What Zia Is
**Zia** is a fast, hybrid voice personal assistant for **Windows**. It automates desktop tasks via spoken commands. 

- **Version:** 0.5.0
- **Platform:** Windows only.
- **LLM Stack**: Cloud API Cascade (HuggingFace, Groq, Gemini, OpenRouter) with Local Fallback (Ollama Llama 3.2 3b).
- **Vision Stack**: Qwen2-VL -> Gemini Flash -> Local Moondream.
- **Execution**: EffGen (RAG/Router), AgentKthx (Agentic OS Execution).

## Key Implementation Details
- **Memory**: We use `effgen.LongTermMemory` backed by `SQLiteStorageBackend` at the repo root.
- **Vision Grounding**: We use minimal prompts for HuggingFace models to prevent hallucinated coordinates.
