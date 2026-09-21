# Zia Personal Assistant - Next Generation Roadmap

This document outlines the *next generation* of improvements for Zia, starting fresh from Phase 1. Now that the core brains and automation hands are built, we are focusing on giving Zia long-term memory, advanced agentic capabilities, a visual presence, and ecosystem connectivity.

---

## Phase 1: Persistent Memory & Context (The "Cheatcode") 🧠
*Currently, Zia's memory resets when the script restarts. We need her to remember things long-term.*

- [ ] **Text-File Memory System**: Create a lightweight, file-based memory system (`.txt` or JSON files) that stores user preferences, past context, and important notes.
- [ ] **Memory Retrieval**: Before Zia answers a prompt, she scans these text files so she always remembers who you are, what projects you are working on, and how you like things done.
- [ ] **Voice-Activated Note Taking**: Allow the user to say *"Zia, remember that my WiFi password is XYZ"* and have her automatically append it to the memory file.

---

## Phase 2: Advanced Agentic Tooling 🛠️
*Move beyond rigid regex patterns and give the LLM the ability to actively "do" things.*

- [ ] **Dynamic Function Calling**: Upgrade the LLM pipeline so the AI can decide which tools to use. If you ask a complex question, the LLM can choose to run a Python script or use the calculator tool itself.
- [ ] **Real-Time Web Search**: Integrate an API (like SerpAPI or Google Search) so Zia can look up live information, news, or documentation rather than relying on offline training data.
- [ ] **File System Agent**: Give the LLM the ability to read, summarize, and securely write to files on your PC based on your conversational requests.

---

## Phase 3: The PC Interface & Visuals 🖥️
*Give Zia a visual presence on the PC rather than just living in the terminal.*

- [ ] **Floating Minimalist GUI**: Build a sleek, transparent overlay (using PyQt or Tkinter) that sits quietly on your screen. It can show a visual sound waveform when she is listening or speaking.
- [ ] **Rich Visual Cards**: When you ask for the weather, a YouTube video, or a code snippet, Zia can display a beautiful, temporary visual card on the screen in addition to speaking.
- [ ] **System Tray Controls**: Add advanced right-click menus to the existing system tray icon for quick toggles (mute, pause proactive monitoring, etc.).

---

## Phase 4: The Mobile & Ecosystem Bridge 📱
*Allow you to interact with Zia when you aren't sitting directly at your keyboard.*

- [ ] **Headless API Server**: Spin up a lightweight FastAPI server in the background so Zia can receive commands over the local network.
- [ ] **Companion Web App**: A local webpage accessible from your phone that acts as a "Zia Remote Control." You can silently type commands, view PC health stats, or trigger routines from your bed.
- [ ] **Webhook Listener**: Allow external services to trigger Zia. For example, if a GitHub Action fails or a Google Calendar event approaches, the API can receive the webhook and Zia will speak the notification out loud.

---

## Phase 5: Cloud APIs & Advanced Integrations ☁️
*Since we are not strictly locking this down to 100% offline, we can plug in powerful cloud services for heavy lifting.*

- [ ] **Hybrid LLM Routing**: Keep the local LLaMA model for fast, everyday tasks, but add API keys for GPT-4 or Claude. Zia can route highly complex coding questions to the cloud models for maximum accuracy.
- [ ] **Ultra-Realistic Voice (Optional)**: Integrate ElevenLabs or OpenAI TTS APIs as an alternative to Piper TTS for incredibly lifelike, emotive voice responses when connected to the internet.
- [ ] **Smart Home Hooks**: Connect Zia's API to Home Assistant or Philips Hue so you can control your physical room lighting when you trigger your "Good morning" or "Hackathon" routines.
