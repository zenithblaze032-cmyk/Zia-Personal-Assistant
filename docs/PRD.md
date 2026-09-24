# Product Requirements Document (PRD)

## Goal
Build a lightning-fast, hybrid voice assistant for Windows that blends macro automation with deep agentic reasoning using an API-first cloud architecture and local resilience.

## States
- **ASLEEP**: Passively listening for the wake word (`wake up`).
- **AWAKE**: Actively processing commands.

## Core Features (v0.5)
- **Hybrid API Routing**: Commands cascade through ultra-fast cloud LLMs, falling back to local instances on failure.
- **Deterministic Routing**: Regex skills for instant actions (volume, open apps).
- **Agentic Executor**: AgentNova for iterative, multi-step problem solving.
- **Vision Engine**: Real-time screen analysis and grounding (clicking buttons autonomously).
