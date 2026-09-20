# Project Context — Zia

Quick-reference memory for anyone (human or agent) working on this codebase.

---

## What Zia Is

**Zia** is a fast, completely **offline** voice personal assistant for **Windows**. It automates desktop tasks via spoken commands — no cloud, no API keys, no subscriptions.

- **Version:** 0.2.x
- **Language:** Python 3.10+
- **Platform:** Windows only (by design)
- **Repo:** `zenithblaze032-cmyk/Jarvis-Personal-Assistant` (originally a Jarvis clone, renamed to Zia)

## Interaction Model

1. User says a wake phrase — **"wake up"**, **"Zia"**, **"Hey Zia"**, **"Jarvis"**, etc. Inline commands work in one breath ("wake up open notepad").
2. While **AWAKE**, commands are dispatched to skills and responses are spoken.
3. **"Go to sleep"** returns to standby; **"Shut down"** exits. Auto-sleeps after 30s idle.

## Architecture Snapshot

```
Zia.py            ← Main loop: audio capture, wake word, state machine
core/
  context.py      ← Context object (ctx.say, ctx.sleep, ctx.shutdown)
  router.py       ← Regex-based skill dispatcher (error-isolated)
  piper_tts.py    ← Offline Piper TTS wrapper (Edge TTS fallback)
skills/
  __init__.py     ← Registers all skill modules
  apps.py         ← Open apps and websites
  system.py       ← Time, date, volume, screenshot, lock, help
  web.py          ← Google and YouTube search
  media.py        ← Media playback controls
```

- **Audio pipeline:** Mic (16 kHz) → gain (×4.0) → Vosk STT (offline) → state check → `Router.dispatch` → skill → `ctx.say` → Piper TTS.
- **Two states:** `ASLEEP` (wake word only) / `AWAKE` (full command dispatch).

## Key Design Decisions (the "why")

| Decision | Reason |
|---|---|
| Mic muted during TTS + 1.5s cooldown | Zia must never hear its own voice (echo feedback) |
| 3s post-wake audio ignore | Wake word echo shouldn't trigger a command |
| Dispatch only on Vosk _Final_ results | Partials cause half-heard false triggers |
| try/except around every skill handler | A broken skill logs an error and speaks a fallback — never crashes Zia |
| Regex routing (for now) | Fast and fully offline; NLP/LLM intent matching is a planned Phase 2 upgrade |
| Models stored in `models/` | ~164 MB one-time download on first run (Vosk + Piper) — never committed |

## Conventions

- Formatting/linting: **Ruff + Black, line length 120** (see `pyproject.toml`).
- Config via `.env` (copy from `.env.example`) — no hardcoded user paths, mic indices, or URLs.
- Module loggers: `logging.getLogger("Zia.<module>")`, never `print()`.
- Adding a skill: new `skills/<name>.py` → register in `skills/__init__.py` → add to Help + README table → changelog entry.
- Full coding rules: see `docs/RULES.md`.

## History Highlights

- **0.1.0** — Initial release: basic offline voice interaction, wake word, hardcoded workspace launcher.
- **0.2.0** — Modular skills system: router, offline wake word, system/media/web skills.
- **0.2.1** — Cleanup: docs split into `docs/`, TTS moved to `core/piper_tts.py`.

## Where to Look

| Question | File |
|---|---|
| How do I use it? | `README.md` |
| How does it work internally? | `docs/ARCHITECTURE.md` |
| What's planned next? | `docs/IMPROVEMENTS.md`, `docs/TASKS.md` |
| What changed recently? | `docs/CHANGES.md` |
| Coding standards | `docs/RULES.md` |
