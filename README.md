# Zia 🎙️

A blazingly fast, hybrid AI-powered personal assistant built exclusively for Windows. Zia moves beyond basic chatbots by integrating deeply into the OS, bridging the gap between natural language and local system automation. 

## 🚀 Core Features

- **Hybrid Architecture**: Fast and accurate voice recognition powered by Google Speech API, while keeping text-to-speech (Piper) local. LLM reasoning cascades through ultra-fast cloud APIs (Groq, Gemini, OpenRouter) for maximum speed, and automatically falls back to local Llama 3.2 models for resilience and offline capability.
- **AgentNova OS Integration**: Zia doesn't just talk; she acts. Powered by AgentKthx, she can minimize/maximize windows, control system volume, press hotkeys, manage files, and execute PowerShell commands.
- **Headless Web Browsing**: Ask a question, and Zia will silently search the web, fetch the HTML, strip out the noise, and read you a concise summary of the page. Includes a **Watchdog Abort System**—just say "Abort task" to instantly cancel any stuck web search.
- **Continuous Memory & NLP**: Uses `spaCy` to instantly perform NLP Entity Extraction on your speech. This gives the LLM absolute certainty on the subjects you are talking about, allowing it to instantly recall facts (like your name or preferences) from the local SQLite database without manual sleep triggers. 
- **Vision Capabilities**: Tell Zia to *"Analyze my screen"* and she uses Moondream Vision models to take a screenshot and tell you exactly what you're looking at.

## 🏗️ Architecture

Zia uses a sophisticated routing engine to ensure sub-second response times:
1. **STT (Speech-to-Text)**: Google Speech API continually listens for the wake word with high accuracy and low latency.
2. **The Router**: 
   - *Deterministic Fast-Path*: Simple commands (e.g., "Take a screenshot", "What's the weather") bypass the LLM entirely using keyword heuristics and execute instantly, doubling response speeds.
   - *NLP RAG Context*: Personal questions trigger `spaCy` to extract entities, query the local database, and inject pinpoint context into the prompt.
   - *AgentNova Executor*: Complex multi-step requests (e.g., "Search Wikipedia") are handed to the AgentKthx loop which iteratively uses OS tools to solve the goal (with Watchdog abort support).
3. **TTS (Text-to-Speech)**: Responses are synthesized via local Piper TTS, with built-in audio echo cancellation so Zia doesn't trigger her own wake word while speaking.

## 🛠️ Installation & Setup

1. **Prerequisites**: 
   - Ensure Python 3.10+ is installed.
   - Install [Ollama](https://ollama.com/) and pull the required models: `ollama run llama3.2` and `ollama run moondream`.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run**:
   Simply execute the batch script to launch the assistant:
   ```cmd
   run.bat
   ```

## 📖 Documentation
- **[Commands Reference](commands.txt)**: A full list of voice commands Zia understands.
- **[Testing Scenarios](testing.md)**: End-to-end manual testing procedures to verify the OS, Web, and RAG subsystems.
- **[Project Roadmap](docs/IMPROVEMENTS.md)**: The phased development plan outlining how Zia was built.
