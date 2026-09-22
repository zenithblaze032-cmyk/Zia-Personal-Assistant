# Zia 🎙️

A fast, fully offline, hybrid personal assistant for Windows. It automates desktop tasks and handles complex OS operations through simple voice commands.

## Architecture Highlights
- **Vosk**: Instant, offline wake word detection.
- **Piper TTS**: Fast, local text-to-speech for seamless conversations.
- **EffGen**: Cognitive complexity router and RAG memory database.
- **AgentKthx (Nova)**: Autonomous local agent for complex shell, file, and web tasks.
- **Llama 3.2**: Powers all local reasoning and generation.

## How it Works
1. Say **"wake up"** to enter listening mode.
2. Issue commands — simple commands are routed via fast Regex, memory queries are injected with RAG, and complex OS tasks are handled by AgentNova.
3. Say **"Go to sleep"** to return to standby, or **"Shut down"** to exit.
