```
# Task: Integrate AgentNova + EffGen + agent-sdk-core into Zia (personal assistant)

## Project Context
Zia is my local personal assistant. Current architecture:

- `zia.py` — main loop + `_dispatch()`
- `core/router.py` — regex-based command dispatcher
- `core/context.py` — service container (`say`, `sleep`, `shutdown`)
- `core/llm.py` — Ollama client (`llama3.2:3b`)
- `core/stt.py` — speech-to-text (may need refactor)
- `core/tts.py` — Edge-TTS output
- `core/state.py` — AssistantState enum + State machine
- `skills/apps.py`, `skills/media.py`, `skills/system.py`, `skills/web.py`, `skills/vision.py` (moondream)
- `core/workspace.py` — window/app launching automation

**Hardware:** i5 13th Gen · RTX 3050 6GB · 24GB RAM  
**VRAM budget:** llama3.2:3b (~2.6 GB) + moondream (~2 GB) + STT (~1.5 GB) ≈ 5–6 GB. Must stay under 6 GB.

## Three frameworks to integrate — each for its strength

| Framework | Role in Zia | What it does |
|---|---|---|
| **agent-sdk-core** | Voice input + memory | `speech_to_text()` for STT, ChromaDB RAG middleware for long-term memory |
| **EffGen** | Brain routing + prompt compression | Complexity analysis, task decomposition, 70–80% prompt compression for llama3.2:3b |
| **AgentNova** | Local tool execution | Shell, file ops, web search with built-in security (path validation, command blocklist, fuzzy tool matching) |

Replio has been **uninstalled** — it was redundant with AgentNova.

## Target Architecture

```
User speaks
    │
    ▼
[agent-sdk-core] speech_to_text()
    │
    ▼
[jarvis._dispatch]
    │
    ├── Router match? → existing skill → TTS  (fast path, unchanged)
    │
    └── No match → [EffGen] complexity routing
                        │
                        ├── Simple → core/llm.py → TTS
                        │
                        └── Complex → [AgentNova] → tools → TTS
```

## Integration Plan

### Layer 1 — Voice Input (`core/stt.py`)
- Wrap `agent_sdk.OllamaClient.speech_to_text()` as the primary STT
- Keep the existing STT as fallback if agent-sdk-core fails
- Output: plain transcript string (same interface as before)
- Do NOT change `core/tts.py` — Edge-TTS stays as-is

### Layer 2 — Brain Routing (`core/brain.py`, new file)
- Use EffGen's complexity router to classify incoming text into:
  - `SIMPLE` → direct LLM call via `core/llm.py`
  - `TOOL` → hand off to AgentNova executor
  - `MULTI_STEP` → EffGen decomposes, then AgentNova executes each step
- Apply EffGen's prompt compression before every LLM call
- Inject relevant memories from agent-sdk-core's RAG middleware into the system prompt

### Layer 3 — Local Execution (`core/executor.py`, new file)
- Wrap AgentNova's agent mode for tool execution
- Enable `confirm_dangerous=True` for destructive ops (file delete, shell rm, etc.)
- Use AgentNova's built-in security: path validation, command blocklist
- Map AgentNova tool results back to `ctx.say()` for TTS output
- Timeout every tool call at 30 seconds

### Integration Points
- `zia._dispatch()` new chain: `Router → Brain → Executor`
- `Context` should expose: `ctx.stt`, `ctx.brain`, `ctx.executor`, `ctx.memory`
- `core/config.py` new flags:
  ```
  USE_EFFGEN=true
  USE_AGENTNOVA=true
  USE_AGENTSDK_STT=true
  AGENTNOVA_CONFIRM_DANGEROUS=true
  AGENTNOVA_TIMEOUT_SEC=30
  EFFGEN_COMPRESS_PROMPTS=true
  ```

## Rules — Do NOT Do These

- Do **not** replace `skills/` with AgentNova tools — keep skills as Router patterns
- Do **not** use agent-sdk-core's chat/tool-calling — use only its **STT** and **RAG middleware**
- Do **not** route simple commands through EffGen — Router must always be tried first
- Do **not** load all three frameworks' models simultaneously — sequential loading only
- Do **not** let AgentNova run shell commands without confirmation on destructive ops

## VRAM Discipline
- Only one LLM/VLM loaded at a time on GPU
- STT can run on CPU if VRAM is tight
- Unload brain model before loading moondream for vision tasks
- Log VRAM after each component load (`nvidia-smi --query-gpu=memory.used --format=csv`)

## Deliverables
1. `core/stt.py` — refactored to use agent-sdk-core, existing STT as fallback
2. `core/brain.py` — EffGen routing + compression + memory injection
3. `core/executor.py` — AgentNova wrapper with security + timeout
4. `core/memory.py` — RAG middleware wrapper (ChromaDB via agent-sdk-core)
5. `core/context.py` — expose `stt`, `brain`, `executor`, `memory`
6. `zia.py` — updated `_dispatch()` with new chain
7. `core/config.py` — feature flags above
8. `requirements.txt` / `pyproject.toml` — remove `replio`, pin the other three

## Test Scenarios
| Input | Expected path | Expected latency |
|---|---|---|
| "open chrome" | Router → skill → TTS | < 200 ms |
| "what's the weather" | Router miss → EffGen SIMPLE → LLM → TTS | < 2 s |
| "find my latest screenshot and describe it" | EffGen MULTI_STEP → AgentNova (file + moondream) → TTS | < 6 s |
| "delete all files in Downloads" | EffGen TOOL → AgentNova with confirm_dangerous → ask user first | safe |

- Verify TTS works on all paths
- Verify VRAM never exceeds 6 GB during any test
- Log every routing decision: `{input, path, framework, latency_ms}`

## Success Criteria
- Zia answers a simple question in under 2 seconds
- Zia executes a multi-step task without crashing
- Zero hard-coded AgentNova/EffGen imports outside `core/brain.py` and `core/executor.py`
- Existing skills still work via Router unchanged
- Total disk footprint of the three frameworks < 500 MB
```