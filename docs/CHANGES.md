# Changelog

## [0.3.0] - The Agentic Upgrade
### Added
- Integrated **EffGen** for RAG long-term memory (`memory.db`) and intent classification.
- Integrated **AgentKthx (Nova)** as an execution engine for complex OS-level and multi-step tasks.
- Implemented a safety state machine that intercepts dangerous keywords (e.g., `delete`) and strictly requires verbal confirmation.
- Optimized TTS interruption/barge-in handling.
- Converted STT pipeline to support `agent-sdk-core` with Google Speech fallback.

## [0.2.1] - Codebase Cleanup & Restructuring
### Added
- Created `docs/` folder to store PRD, Architecture, and Rules.
