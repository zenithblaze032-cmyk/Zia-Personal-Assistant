# Product Requirements Document (PRD)

## Goal
Build a fast, offline voice assistant for Windows that blends fast macro automation with deep agentic reasoning.

## States
- **ASLEEP**: Passively listening for the wake word (`wake up zia`).
- **AWAKE**: Actively processing commands.

## Core Features (v0.3)
- **Offline Wake Word**: Vosk for instant wake detection.
- **Hybrid Routing**: Regex skills for instant actions (volume, open apps); LLMs for complex actions.
- **RAG Memory**: Persistent, searchable vector memory using EffGen.
- **Agentic OS Control**: Uses AgentKthx to manipulate files, read data, and summarize web content autonomously.
- **Safety**: Strict confirmation block on destructive commands.
