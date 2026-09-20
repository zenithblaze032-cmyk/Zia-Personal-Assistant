# Zia 🎙️

A fast, completely offline personal assistant for Windows. It automates desktop tasks through simple voice commands — no cloud, no API keys, no subscriptions.

## How it Works

1. Say **"wake up"** (or just "wake up Zia") to wake it up.
2. Issue commands — Zia will respond and act immediately.
3. Say **"Go to sleep"** to put it back in standby, or **"Shut down"** to exit.
4. Auto-sleeps after 30 seconds of inactivity.

## Features & Capabilities

### Wake Up

- **Phrases:** "Wake up", "Zia", "Hey Zia", "Arise", "Okiro", "Okiru", and all Jarvis forms ("Jarvis", "Hey Jarvis", …)
- **Inline support:** Say a command right after the wake word — "wake up open notepad" works in one breath.

### Built-in Skills (v0.2)

| Skill          | Say this...                         | Zia will...                                      |
| -------------- | ----------------------------------- | ------------------------------------------------ |
| **Workspace**  | _"Let's get back to work"_          | Open LeetCode, YouTube, and VS Code side-by-side |
| **Apps**       | _"Open notepad"_ / _"Open Spotify"_ | Launch any installed app by name                 |
| **Sites**      | _"Open YouTube"_ / _"Open GitHub"_  | Open any website in your default browser         |
| **Web Search** | _"Search for Python tutorials"_     | Perform a Google search                          |
| **YouTube**    | _"Play lo-fi on YouTube"_           | Perform a YouTube search                         |
| **System**     | _"What's the time?"_ / _"Date?"_    | Speak the current time/date                      |
| **Volume**     | _"Volume up"_ / _"Mute"_            | Control system volume                            |
| **Media**      | _"Pause"_ / _"Next track"_          | Control media playback (global media keys)       |
| **Utility**    | _"Take a screenshot"_               | Save a screenshot to Pictures/Zia                |
| **Security**   | _"Lock my screen"_                  | Lock the PC workstation                          |
| **Help**       | _"Who are you"_ / _"What can you do"_ | Introduce itself and summarize capabilities      |
| **Sleep**      | _"Go to sleep"_                     | Return to standby mode                           |
| **Exit**       | _"Shut down"_                       | Exit the program with a goodbye                  |

## Architecture

Zia uses a central listening loop with a modular skills system:

```text
Zia.py          ← Main loop: audio capture, wake word, state machine
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
   python Zia.py
   ```
   _(First run downloads the offline speech models — ~164 MB, one-time only.)_

## Customization

Copy `.env.example` → `.env` and edit any values to override defaults.

Key settings:
| Setting | Default | What it does |
|---|---|---|
| `WAKE_WORD` | `wake up` | The phrase that wakes Zia up |
| `IDLE_TIMEOUT_S` | `30` | Seconds before auto-sleeping when idle |
| `LEETCODE_URL` | LeetCode problems | Left tile URL |
| `YOUTUBE_PLAYLIST_URL` | Playlist URL | Centre tile URL |
| `VSCODE_OPEN_PATH` | `D:\Development` | VS Code folder |
| `MIC_GAIN_FACTOR` | `4.0` | Raise if Zia misses soft speech |
| `Zia_INPUT_DEVICE` | auto | Mic index or name to use |

## Troubleshooting

| Problem                   | Fix                                                        |
| ------------------------- | ---------------------------------------------------------- |
| Zia misses my voice       | Raise `MIC_GAIN_FACTOR` to `6.0`                           |
| False triggers from noise | Lower `MIC_GAIN_FACTOR` to `2.0`                           |
| Wrong mic selected        | Set `Zia_INPUT_DEVICE` in `.env`                           |
| TTS is silent             | First run downloads the Piper model (~114 MB) — check logs |
| Chrome/VS Code not tiling | Check they are installed and `code` is on PATH             |
