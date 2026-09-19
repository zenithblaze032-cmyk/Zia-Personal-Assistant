# System Architecture

Jarvis is structured as a central listening loop (`jarvis.py`) with a modular skills system.

## Directory Layout

```
jarvis.py          ← Main loop: audio capture, wake word, state machine
core/
  context.py       ← Context object (ctx.say, ctx.sleep, ctx.shutdown)
  router.py        ← Regex-based skill dispatcher
  piper_tts.py     ← Offline Piper TTS wrapper
skills/
  __init__.py      ← Registers all skill modules
  apps.py          ← Open apps and websites
  system.py        ← Time, date, volume, screenshot, lock, help
  web.py           ← Google and YouTube search
  media.py         ← Media playback controls
```

## State Machine

Jarvis has two states:

```
ASLEEP ──── "Jarvis" (wake word) ────► AWAKE
  ▲                                      │
  │         "Go to sleep"                │ Commands dispatched
  └──────────────────────────────────────┘ to Router
  ▲
  └── Idle for 30s (auto-sleep)
```

## Audio Pipeline

```
Microphone (16 kHz)
  → Gain amplification (×4.0)
  → Vosk STT (offline, local)
  → State machine check
  → Router.dispatch(text, ctx)
  → Skill handler
  → ctx.say(response)
  → Piper TTS (offline) or Edge TTS (fallback)
```

## Key Design Decisions

- **Mic muting during TTS**: While Jarvis speaks, the microphone loop is paused + a 1.5s cooldown after — so Jarvis never hears its own voice.
- **Post-wake cooldown**: After waking up, audio is ignored for 3 seconds so the wake word's own echo doesn't trigger a command.
- **Final-only dispatch**: Commands only fire on Vosk's *Final* results (not partials) to prevent half-heard words triggering actions.
- **Error isolation**: Each skill handler is wrapped in try/except inside the Router — a broken skill never crashes Jarvis.
