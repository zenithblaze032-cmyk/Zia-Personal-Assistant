# Tasks & Progress — Zia

Working task tracker for active and completed work. Long-term ideas live in `IMPROVEMENTS.md`; completed releases are recorded in `CHANGES.md`.

---

## ✅ Completed

### v0.2.x — Modular Skills System

- [x] Offline wake word detection (Vosk)
- [x] Regex-based skills router with error isolation (`core/router.py`)
- [x] App & website launching by voice
- [x] Google & YouTube voice search
- [x] System controls: time, date, volume, screenshot, screen lock
- [x] Media controls: play/pause, next/previous (global media keys)
- [x] Tiled workspace launcher (LeetCode + YouTube + VS Code)
- [x] Piper TTS (offline) with Edge TTS fallback
- [x] Smart mic muting during TTS + post-wake cooldown
- [x] Idle auto-sleep (30s timeout)
- [x] `docs/` folder: PRD, architecture, changelog split out
- [x] Moved `src/tts.py` → `core/piper_tts.py`

---

## 🔄 In Progress

_(nothing currently)_

---

## 📋 Backlog / Next Up

Pulled from `IMPROVEMENTS.md` Phase 1 — everyday utilities:

- [ ] **Weather & news skill** — _"What's the weather?"_ / _"Read the headlines"_
- [ ] **Alarms & timers** — background timer skill with audio alert
- [ ] **Clipboard manager** — read/save clipboard by voice
- [ ] **Custom wake word training** — back to `openwakeword` with a custom `hey_Zia.onnx` model

Later phases (see `IMPROVEMENTS.md` for details):

- [ ] Local LLM integration (Ollama) for general Q&A
- [ ] Conversation context memory ("play the second one")
- [ ] Fuzzy intent matching to replace strict regex
- [ ] Smart home / MQTT control
- [ ] Screen-context vision assistant (LLaVA)
- [ ] Routines & proactive notifications
- [ ] Local HTTP API for mobile/Stream Deck triggers

---

## 🐛 Known Issues

_(none reported)_
