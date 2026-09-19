# Changelog

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
- Wake word "Jarvis" support.
- Hardcoded workspace tiled launch.
