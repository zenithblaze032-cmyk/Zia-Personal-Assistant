# System Architecture

Zia is structured as a central listening loop (`Zia.py`) with a hybrid routing and multi-agent system.

## Directory Layout
```text
Zia.py          ← Main loop: audio capture, state machine
core/
  asr.py           ← ASR pipeline (Google Speech + Agent-SDK fallback)
  brain.py         ← EffGen complexity router & prompt compression
  context.py       ← Context object passed to skills
  executor.py      ← AgentKthx (Nova) wrapper with safety limits and OS/Web tools
  llm.py           ← Llama 3.2 bindings
  memory.py        ← EffGen RAG Database wrapper and Background Consolidation Agent
  router.py        ← Regex-based skill dispatcher
skills/            ← Fast-path local regex tools
```

## Processing Flow
1. **Audio Capture**: `core/asr.py` handles chunked listening.
2. **Regex Router**: Tries to match fast skills (e.g. screenshot, volume) via `core/router.py`.
3. **Brain Routing**: Unmatched commands hit `core/brain.py` (EffGen) to classify as `SIMPLE` or `MULTI_STEP`.
4. **Execution**:
   - `SIMPLE`: RAG memory injected -> Llama 3.2 answers directly.
   - `MULTI_STEP`: Sent to `core/executor.py` (AgentNova) to perform OS actions with shell tools.
