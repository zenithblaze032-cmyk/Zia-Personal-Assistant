# Changelog

## [0.5.0] - The Hybrid Cloud Architecture
### Added
- **Hybrid API Cascade**: Merged `llm.py` and `llm_zen.py` into a unified Hybrid API generator. Zia now automatically cascades through HuggingFace, Groq, Gemini, and OpenRouter for lightning-fast reasoning, and safely falls back to local Ollama if offline.
### Removed
- **Zen Mode**: Removed the manual voice toggle for Zen Mode. The system is now API-first by default.
- **WhatsApp Messaging Automation**: Completely removed `whatsapp.py` and messaging dependencies as the browser automation proved too fragile for production use.
### Fixed
- **Vision Grounding**: Optimized grounding prompts for Qwen-VL to improve UI interaction accuracy.
- **YouTube Search**: Upgraded YouTube skills to extract exact video IDs instead of opening search result pages.

## [0.4.1] - The Reliability & NLP Upgrade
### Added
- Added **Watchdog Abort System**: A global abort event that can instantly cancel stuck AgentNova web searches or loops.
- Added **Intent & Entity Extraction**: Created `core/nlp.py` using `spaCy` to instantly extract context from voice commands.
