# Product Requirements Document (PRD)

## Goal

Build a fast, completely offline voice assistant for Windows that automates desktop tasks using simple, natural voice commands.

## States

- **ASLEEP**: Passively listening for the wake word only.
- **AWAKE**: Actively processing commands through the skills router.

## Core Features (v0.2)

- **Offline wake word**: Instantly detects "Zia" without cloud latency (Vosk).
- **Modular skills**: Commands are routed to independent skill modules — easy to extend.
- **App/site launching**: Open any app or website by name.
- **Web search**: Google and YouTube search by voice.
- **System control**: Volume, time/date, screenshot, screen lock.
- **Media control**: Play/pause, next/previous track via global media keys.
- **Tiled workspace**: Snap LeetCode, YouTube, and VS Code into a 3-column layout.
- **Smart listening**: Mic is muted during TTS to prevent echo feedback.
- **Idle dozing**: Auto-sleeps after 30 seconds of inactivity.
- **Graceful exit**: Speaks goodbye on both voice command and Ctrl+C.

## Non-Goals

- Cloud API reliance (no keys, no subscriptions, no internet required to function).
- General-purpose chatbot (Zia is an _operator_, not an encyclopedia — yet).
