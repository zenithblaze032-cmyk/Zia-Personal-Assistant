# Zia Voice Command Reference

Zia is an offline voice assistant for Windows. All commands below are spoken after waking Zia up. Unmatched phrases are forwarded to the local LLM fallback, so Zia will attempt a conversational answer for anything not listed here.

## Command Table

| Command / Trigger Phrase | Action |
| :--- | :--- |
| **Wake Commands** | |
| `wake up`, `wake up zia`, `jarvis`, `arise` | Wakes Zia from standby mode |
| `go to sleep`, `standby`, `sleep` | Returns Zia to standby mode |
| `shut down`, `exit`, `quit`, `close` | Exits the Zia application entirely |
| `ok zia`, `stop talking`, `shut up` | Interrupts Zia and stops TTS playback |
| **Workspaces & Routines** | |
| `start dsa`, `open data structures` | Opens DSA workspace (LeetCode + YouTube + VS Code) |
| `start development`, `open web dev` | Opens Web-dev workspace (W3Schools + YouTube + VS Code) |
| `start jarvis work` | Opens Zia-project workspace (VS Code + Antigravity) |
| `start hackathon` | Opens Hackathon workspace (VS Code + Antigravity) |
| **System Controls** | |
| `what's the time`, `time` | Speaks the current local time |
| `what's the date`, `date` | Speaks today's full date |
| `screenshot`, `take a screenshot` | Takes a full-screen screenshot |
| `read my screen`, `what is on my screen` | Uses AI Vision to analyze and describe the screen |
| `lock my screen`, `lock my pc` | Locks the Windows workstation |
| `volume up`, `louder` | Increases system volume |
| `volume down`, `quieter` | Decreases system volume |
| `mute`, `silence`, `shut up` | Toggles system mute (if Zia is not speaking) |
| **Media Playback** | |
| `play`, `pause`, `resume` | Play/Pause media across apps (Spotify, Chrome, VLC) |
| `next`, `skip track` | Skips to the next track/video |
| `previous`, `go back` | Goes back to the previous track/video |
| `stop playback`, `stop music` | Stops media playback |
| **Web & Applications** | |
| `google <query>` | Opens a Google search for the query |
| `play <query> on youtube` | Opens a YouTube search for the query |
| `open <app/website>`, `launch <app>` | Opens standard apps (Chrome, Notepad) or sites (YouTube, Gmail) |
| `what is the weather`, `weather today` | Speaks the current temperature for your location |
| **Productivity** | |
| `set a timer for <N> minutes/seconds` | Sets a background timer and notifies when up |
| `take a note that <note>`, `remember <note>` | Saves a timestamped note to memory.txt |
| `read my clipboard` | Speaks the current clipboard contents |
| `save my clipboard` | Saves clipboard contents to local.txt |
| **Window Management** | |
| `snap <app> to the left` | Snaps a matching window to the left half of the screen |
| `snap <app> to the right` | Snaps a matching window to the right half of the screen |
| `maximize <app>` | Maximizes a matching window |
| **Automation** | |
| `move mouse <direction> by <N>` | Moves the mouse cursor relative to its current position |
| `click`, `right click`, `double click` | Performs a mouse click |
| `press <key>` | Presses a keyboard key (enter, space, escape, etc.) |
| `type <text>` | Types the specified text into the focused window |
| `write a(n) <doc> about <topic>` | AI drafts content and types it directly into the focused window |
| **Identity & Help** | |
| `who are you`, `help`, `commands` | Zia introduces herself and summarizes her capabilities |

*File generated programmatically. Last updated after resolving voice command bugs.*
