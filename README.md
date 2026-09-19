# JARVIS 🎙️

A fast, completely offline personal assistant for Windows. It automates desktop tasks through simple voice commands — no cloud, no API keys, no subscriptions.

## How it Works

1. Say **"Jarvis"** (or "Hey Jarvis") to wake it up.
2. Issue commands — Jarvis will respond and act immediately.
3. Say **"Go to sleep"** to put it back in standby, or **"Shut down"** to exit.
4. Auto-sleeps after 30 seconds of inactivity.

## Features & Capabilities

### Wake Up
- **Phrases:** "Jarvis", "Hey Jarvis", "Hi Jarvis", "Ok Jarvis"
- **Inline support:** Say a command right after the wake word — "Hey Jarvis open notepad" works in one breath.

### Built-in Skills (v0.2)

| Skill | Say this... | Jarvis will... |
|---|---|---|
| **Workspace** | *"Let's get back to work"* | Open LeetCode, YouTube, and VS Code side-by-side |
| **Apps** | *"Open notepad"* / *"Open Spotify"* | Launch any installed app by name |
| **Sites** | *"Open YouTube"* / *"Open GitHub"* | Open any website in your default browser |
| **Web Search** | *"Search for Python tutorials"* | Perform a Google search |
| **YouTube** | *"Play lo-fi on YouTube"* | Perform a YouTube search |
| **System** | *"What's the time?"* / *"Date?"* | Speak the current time/date |
| **Volume** | *"Volume up"* / *"Mute"* | Control system volume |
| **Media** | *"Pause"* / *"Next track"* | Control media playback (global media keys) |
| **Utility** | *"Take a screenshot"* | Save a screenshot to Pictures/Jarvis |
| **Security**| *"Lock my screen"* | Lock the PC workstation |
| **Help** | *"Help"* | List all capabilities |
| **Sleep** | *"Go to sleep"* | Return to standby mode |
| **Exit** | *"Shut down"* | Exit the program with a goodbye |

## Architecture

Jarvis uses a central listening loop with a modular skills system:

```text
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

- **Audio Pipeline:** Microhpone → Gain amplification → Vosk STT (offline) → Router.dispatch → Skill handler → Piper TTS (offline)
- **Smart muting:** Mic is muted during TTS to prevent echo feedback.

## Quick Start

1. Install requirements:
   ```bat
   python -m pip install -r requirements.txt
   ```
2. Double-click `run.bat` or run:
   ```bat
   python jarvis.py
   ```
*(First run downloads the offline speech models — ~164 MB, one-time only.)*

## Customization

Copy `.env.example` → `.env` and edit any values to override defaults.

Key settings:
| Setting | Default | What it does |
|---|---|---|
| `WAKE_WORD` | `jarvis` | The word that wakes Jarvis up |
| `IDLE_TIMEOUT_S` | `30` | Seconds before auto-sleeping when idle |
| `LEETCODE_URL` | LeetCode problems | Left tile URL |
| `YOUTUBE_PLAYLIST_URL` | Playlist URL | Centre tile URL |
| `VSCODE_OPEN_PATH` | `D:\Development` | VS Code folder |
| `MIC_GAIN_FACTOR` | `4.0` | Raise if Jarvis misses soft speech |
| `JARVIS_INPUT_DEVICE` | auto | Mic index or name to use |

## Troubleshooting

| Problem | Fix |
|---|---|
| Jarvis misses my voice | Raise `MIC_GAIN_FACTOR` to `6.0` |
| False triggers from noise | Lower `MIC_GAIN_FACTOR` to `2.0` |
| Wrong mic selected | Set `JARVIS_INPUT_DEVICE` in `.env` |
| TTS is silent | First run downloads the Piper model (~114 MB) — check logs |
| Chrome/VS Code not tiling | Check they are installed and `code` is on PATH |
