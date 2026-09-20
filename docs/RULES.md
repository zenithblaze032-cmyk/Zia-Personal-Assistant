# Coding Rules — Zia

Guidelines every change to this codebase must follow.

---

## 1. Project Principles

- **Offline-first**: Zia runs with zero cloud dependencies. No API keys, no network calls at runtime. If a feature needs the internet, it must degrade gracefully (see Edge TTS fallback) and never block startup.
- **Fast & quiet**: Every skill should respond within ~1 second. Never add artificial delays.
- **Error isolation**: A broken skill must never crash Zia. The Router wraps every handler in try/except and speaks a fallback line ("Something went wrong, sir."). Skill handlers should let exceptions propagate to the Router rather than swallowing them silently.
- **Windows-only is fine**: Zia targets Windows desktops. Use `os.startfile`, `pyautogui`, `pygetwindow`, etc. freely — no cross-platform gymnastics required.

## 2. Python Style

- **Python 3.10+** (`target-version = py310`). Modern syntax allowed: match statements, `X | None` unions, f-strings.
- **Formatting**: Black + Ruff, **line length 120** (configured in `pyproject.toml`).
- **Linting**: Ruff with `E, F, W, I` rules selected — fix import ordering (`I`) and unused imports (`F`) before committing.
- **Type hints**: Annotate public functions and handler signatures. Use `from __future__ import annotations` at the top of modules.
- **Typing imports**: Use `TYPE_CHECKING` guard for imports that are only needed for annotations (see `core/router.py` for the pattern).
- **Logging**: Use module-level loggers named after the component: `log = logging.getLogger("Zia.<module>")`. Never use bare `print()`.

## 3. Skills Architecture

- **One skill domain per module** in `skills/` (apps, web, system, media).
- **Skills are data, not classes**: each skill module registers `(regex_pattern, handler)` pairs with the Router. Registration happens in `skills/__init__.py`.
- **Handler signature**: `def handler(match: re.Match, ctx: Context) -> None`. The Router passes the regex match and the context object.
- **Case-insensitive patterns**: Register patterns without flags — the Router compiles them with `re.IGNORECASE` by default.
- **Never dispatch on partials**: Handlers must only rely on Vosk _Final_ results passed through the Router, never raw partial transcripts.
- **Speaking responses**: Always respond through `ctx.say(...)`. Never call the TTS wrapper directly from a skill.
- **New skills checklist**:
  1. Create `skills/<name>.py`
  2. Register patterns/handlers in `skills/__init__.py`
  3. Add the skill to the Help skill's capability list
  4. Update `README.md` skill table and `docs/CHANGES.md`

## 4. Configuration

- All user-tunable values live in `.env` (see `.env.example`) and are read via environment variables with sane defaults. Never hardcode user-specific paths, mic indices, or URLs in code.
- New settings must be documented in the README's customization table and added to `.env.example`.

## 5. Documentation

- `README.md` is the source of truth for users.
- `docs/` holds internal docs: `PRD.md`, `ARCHITECTURE.md`, `RULES.md` (this file), `TASKS.md`, `MEMORY.md`, `CHANGES.md`, `IMPROVEMENTS.md`.
- Every user-visible change gets a `docs/CHANGES.md` entry (Keep a Changelog format).
- Keep the directory-layout diagrams in `README.md` and `docs/ARCHITECTURE.md` in sync when files move.

## 6. Testing & Hygiene

- Tests live in `tests/` and run via `pytest`. Router dispatch logic is the primary unit-test target.
- Never commit: `__pycache__/`, `.cache/`, `.pytest_cache/`, `.ruff_cache/`, `models/` (downloaded speech models), `venv/`, `.env` (secrets).
- Run `ruff check .` and `ruff format --check .` before committing.
