# Zia Personal Assistant - Roadmap & Improvements

This document outlines a 5-phase roadmap to evolve Zia from a basic voice-activated launcher into a highly advanced, context-aware AI assistant.

---

## Phase 1: Expanding the Basics (Everyday Utilities) 🛠️

_Focus on adding skills that make daily workflows smoother without needing complex AI._

- [ ] **Weather & News Skill**: Integrate a simple API (like OpenWeatherMap) to handle queries like _"What's the weather today?"_ or _"Read me the top tech headlines."_
- [ ] **Alarms & Timers**: Add a skill to set background timers (_"Set a timer for 15 minutes"_) or alarms, triggering audio playback when the time is up.
- [ ] **Clipboard Manager**: A utility skill to manage the clipboard. Example: _"Zia, read my clipboard"_ or _"Save my clipboard to notes."_
- [ ] **Custom Wake Word Training**: Transition from the Google Speech API fallback back to `openwakeword` by training a custom `hey_Zia.onnx` model so the wake word processing happens entirely locally.

---

## Phase 2: Smarter Understanding (The Brains) 🧠

_Focus on moving beyond rigid regular expressions (regex) to actual language understanding._

- [ ] **Local LLM Integration**: Integrate a local LLM (like Llama-3 via Ollama) so Zia can answer general knowledge questions, brainstorm ideas, and parse complex intents offline.
- [ ] **Context Memory**: Implement a short-term memory buffer so Zia remembers the context of the conversation. (e.g., If you say _"Search YouTube for Python tutorials"_, and then say _"Play the second one"_, Zia understands what "the second one" refers to).
- [ ] **Fuzzy Intent Matching**: Replace strict regex routers with lightweight NLP (like `spaCy` or local text embeddings) to classify intents naturally.

---

## Phase 3: Advanced Automation & Vision 👁️

_Focus on giving Zia control over the physical environment and screen content._

- [ ] **Window & OS Management**: Deepen OS integration to arrange the screen dynamically. (_"Snap VS Code to the left and Chrome to the right"_).
- [ ] **Screen Context Awareness (Vision LLM)**: Integrate a local vision model (like LLaVA). When asked _"Why is this code throwing an error?"_, Zia takes a background screenshot, analyzes the active window, and speaks the solution.

---

## Phase 4: Proactive Assistant & Routines ⏰

_Focus on making Zia act without explicit prompts._

- [ ] **Custom Routines**: Chain multiple skills together into triggers. Saying _"Good morning, Zia"_ could read the daily schedule, announce the weather, and open the development workspace.
- [ ] **Proactive Notifications**: Allow background threads to push spoken notifications to Zia. (e.g., _"Sir, your build has finished successfully"_ or _"You have an upcoming meeting in 10 minutes"_).
- [ ] **System Monitoring**: Background monitoring of PC resources. If temperatures or RAM usage get too high, Zia proactively warns: _"Sir, memory usage is at 98%, should I close some background tabs?"_

---

## Phase 5: The Ecosystem (Going Beyond the PC) 🌐

_Focus on accessing Zia from anywhere and ensuring security._

- [ ] **Local HTTP API**: Expose a local REST API or WebSocket server so commands can be triggered from mobile apps, iOS Shortcuts, or Stream Decks.
- [ ] **Multi-Room Microphones**: Build cheap ESP32 satellite microphones for other rooms. Audio spoken in the kitchen is streamed to the PC, and Zia responds through a network-connected kitchen speaker.
- [ ] **Speaker Verification (Voice ID)**: Train the wake word engine to recognize the unique voice signature of the primary user, ensuring unauthorized people cannot issue sensitive commands.
