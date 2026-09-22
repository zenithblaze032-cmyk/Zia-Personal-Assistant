# Coding Rules — Zia

## 1. Project Principles
- **Offline-first**: Zero cloud dependencies where possible. Run models locally via Ollama.
- **Fast & Quiet**: Fast path (regex) skills must execute in <1s.
- **Safety First**: Autonomous file and shell tools must be guarded by confirmation state machines.

## 2. Python Style
- **Python 3.10+**
- **Formatting**: Black + Ruff, line length 120.

## 3. Tool Usage Constraints
- **AgentKthx**: Use only built-in tools. Do not write custom bash scripts inside agent instructions; use the native `shell` tool.
- **EffGen**: Keep `use_tools=False` during intent classification to avoid hallucinated executions.
