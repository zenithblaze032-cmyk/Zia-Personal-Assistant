# Project Context — Zia

Quick-reference memory for anyone working on this codebase.

## What Zia Is
**Zia** is a fast, offline voice personal assistant for **Windows**. It automates desktop tasks via spoken commands. 

- **Version:** 0.3.0
- **Platform:** Windows only.
- **LLM Stack**: Ollama (Llama 3.2 3b), EffGen (RAG/Router), AgentKthx (Agentic OS Execution).

## Key Implementation Details
- **Memory**: We use `effgen.LongTermMemory` backed by `SQLiteStorageBackend` at the repo root (`memory.db`). Retrieval is instantaneous and heavily augmented by `spaCy` NLP extraction, skipping strict SQL queries for flawless continuous fact injection.
- **Safety**: `AgentNovaExecutor` acts as a sandbox. Any command with words like `delete` pauses the agent until the user explicitly says `proceed`.
- **Tools**: Skills are fast-path regex matches. Complex reasoning hits `agentkthx` which is granted OS tool access (`shell`, `list_directory`, etc.).
