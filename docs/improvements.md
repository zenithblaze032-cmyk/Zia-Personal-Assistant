# Jarvis Personal Assistant - Roadmap & Improvements

This document outlines a 5-phase roadmap to evolve Jarvis from a basic voice-activated launcher into a highly advanced, context-aware AI assistant.

---

## Phase 1: Expanding the Basics (Everyday Utilities) 🛠️
*Focus on adding skills that make daily workflows smoother without needing complex AI.*

- [ ] **Weather & News Skill**: Integrate a simple API (like OpenWeatherMap) to handle queries like *"What's the weather today?"* or *"Read me the top tech headlines."*
- [ ] **Alarms & Timers**: Add a skill to set background timers (*"Set a timer for 15 minutes"*) or alarms, triggering audio playback when the time is up.
- [ ] **Clipboard Manager**: A utility skill to manage the clipboard. Example: *"Jarvis, read my clipboard"* or *"Save my clipboard to notes."*
- [ ] **Custom Wake Word Training**: Transition from the Google Speech API fallback back to `openwakeword` by training a custom `hey_jarvis.onnx` model so the wake word processing happens entirely locally.

---

## Phase 2: Smarter Understanding (The Brains) 🧠
*Focus on moving beyond rigid regular expressions (regex) to actual language understanding.*

- [ ] **Local LLM Integration**: Integrate a local LLM (like Llama-3 via Ollama) so Jarvis can answer general knowledge questions, brainstorm ideas, and parse complex intents offline.
- [ ] **Context Memory**: Implement a short-term memory buffer so Jarvis remembers the context of the conversation. (e.g., If you say *"Search YouTube for Python tutorials"*, and then say *"Play the second one"*, Jarvis understands what "the second one" refers to).
- [ ] **Fuzzy Intent Matching**: Replace strict regex routers with lightweight NLP (like `spaCy` or local text embeddings) to classify intents naturally.

---

## Phase 3: Advanced Automation & Vision 👁️
*Focus on giving Jarvis control over the physical environment and screen content.*

- [ ] **Smart Home Control**: Add an MQTT client or hook into Home Assistant APIs to control local IoT devices (*"Dim the room lights"*, *"Turn on the fan"*).
- [ ] **Window & OS Management**: Deepen OS integration to arrange the screen dynamically. (*"Snap VS Code to the left and Chrome to the right"*).
- [ ] **Screen Context Awareness (Vision LLM)**: Integrate a local vision model (like LLaVA). When asked *"Why is this code throwing an error?"*, Jarvis takes a background screenshot, analyzes the active window, and speaks the solution.

---

## Phase 4: Proactive Assistant & Routines ⏰
*Focus on making Jarvis act without explicit prompts.*

- [ ] **Custom Routines**: Chain multiple skills together into triggers. Saying *"Good morning, Jarvis"* could read the daily schedule, announce the weather, and open the development workspace.
- [ ] **Proactive Notifications**: Allow background threads to push spoken notifications to Jarvis. (e.g., *"Sir, your build has finished successfully"* or *"You have an upcoming meeting in 10 minutes"*).
- [ ] **System Monitoring**: Background monitoring of PC resources. If temperatures or RAM usage get too high, Jarvis proactively warns: *"Sir, memory usage is at 98%, should I close some background tabs?"*

---

## Phase 5: The Ecosystem (Going Beyond the PC) 🌐
*Focus on accessing Jarvis from anywhere and ensuring security.*

- [ ] **Local HTTP API**: Expose a local REST API or WebSocket server so commands can be triggered from mobile apps, iOS Shortcuts, or Stream Decks.
- [ ] **Multi-Room Microphones**: Build cheap ESP32 satellite microphones for other rooms. Audio spoken in the kitchen is streamed to the PC, and Jarvis responds through a network-connected kitchen speaker.
- [ ] **Speaker Verification (Voice ID)**: Train the wake word engine to recognize the unique voice signature of the primary user, ensuring unauthorized people cannot issue sensitive commands.
