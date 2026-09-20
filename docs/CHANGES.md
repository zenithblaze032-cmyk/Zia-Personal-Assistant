# Changelog

## [Unreleased]

### Changed

- Replaced the "What can you do" help listing with a professional identity intro. Phrases like _"Who are you?"_, _"What's your name?"_, or _"Introduce yourself"_ now respond with an introduction — "I am Zia, and I am your personal assistant…" — followed by a summary of capabilities. _"What can you do?"_ and _"Help"_ still route to the same intro.

## [0.2.1] - Codebase Cleanup & Restructuring

### Added

- Created `docs/` folder to store PRD, Architecture, and Changes documents separately.
- Regenerated Graphify insights to reflect the latest codebase structure.

### Changed

- Consolidated `README.md` to be the primary source of truth.
- Moved `src/tts.py` to `core/piper_tts.py` to keep backend core logic unified.

### Removed

- Cleaned up auto-generated cache directories (`__pycache__`, `.cache`, `.pytest_cache`, `.ruff_cache`).
- Deleted unused `tests/` directory.

## [0.2.0] - Modular Skills System

### Added

- Modular skills router to dispatch voice commands.
- Offline wake word detection (Vosk).
- Voice controls for system (time, volume, lock, screenshot) and media (play, pause, next).
- App and web search launching via voice commands.

## [0.1.0] - Initial Release

### Added

- Basic offline voice interaction.
- Wake word "Zia" support.
- Hardcoded workspace tiled launch.
