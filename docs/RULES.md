# Coding Rules — Zia

## 1. Project Principles
- **Hybrid-first**: Use ultra-fast Cloud APIs first (via the fallback cascade in `llm.py`), fallback to Ollama locally.
- **Fast & Quiet**: Fast path (regex) skills must execute in <1s.
- **Safety First**: Autonomous file and shell tools must be guarded by confirmation state machines.

## 2. Python Style
- **Python 3.10+**
- **Formatting**: Black + Ruff, line length 120.

## 3. Tool Usage Constraints
- **AgentKthx**: Use only built-in tools.
- **Vision**: Always use short, concise prompts for grounding coordinates to prevent HuggingFace models from hallucinating.
