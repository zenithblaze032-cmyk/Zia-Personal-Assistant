# MASTER ENGINEERING SPECIFICATION: CLOVIS

> **Document Type:** System Architecture & Engineering Blueprint  
> **Project Title:** Clovis Personal Assistant  
> **Core Philosophy:** Deterministic software first, models where intelligence is actually needed.

---

## 1. PROJECT EXECUTIVE OVERVIEW

**Clovis** is a cross-platform personal assistant engineered for absolute reliability, observability, and graceful degradation. Unlike basic wrappers that blindly pass user input to an LLM and execute the output, Clovis treats LLMs as isolated specialist tools within a highly structured, fault-tolerant Python architecture.

### 1.1 Core Engineering Principles
1. **Deterministic-First**: If an OS API can do it (e.g., open a file), use Python. Do not ask an LLM to invent shell commands.
2. **Subsystem Isolation**: A voice failure must not kill the text interface. An agent crash must not kill the assistant.
3. **Observability**: Every action requires an intent, execution plan, timeout, cancellation path, and explicit verification.
4. **Outcome-Oriented Planning**: The user provides a goal ("Organize files"); the system plans constraints and executes via robust task managers.

---

## 2. SYSTEM ARCHITECTURE & COMPONENT BREAKDOWN

Clovis operates on an Event-Driven architecture connected by a central Event Bus.

### 2.1 The Execution Pipeline
1. **User Input** (Voice / Text)
2. **Conversation Runtime & Context**: Gathers memory, user state, and current machine state.
3. **NLP Engine**: Offline intent and entity extraction.
4. **Determinator**: Decides the execution path (e.g., deterministic OS adapter vs. reasoning model vs. memory lookup).
5. **Planner**: Breaks the goal into structured, verifiable steps.
6. **Task Manager**: Executes steps. Handles timeouts, cancellations, and recovery via a Watchdog.
7. **Response Generator**: Generates the final output and logs useful evidence for learning.

### 2.2 Task Management & Reliability
Every side-effecting action is recorded in an **Action Journal** to enable crash recovery. Tasks are strictly managed with:
- **Timeouts**: Operation limits, step limits, and overall deadlines.
- **Watchdog**: Detects if tasks are stuck (distinguishing between long operations vs. crashed processes).
- **Verification**: Explicit checks to ensure an action worked (e.g., checking if a browser process actually started and a page loaded).
- **Idempotency Classification**: Actions are tagged as Safe to repeat, Conditionally repeatable, or Dangerous (requires user confirmation).

### 2.3 Evidence-Based Learning
Clovis does not instantly change its behavior based on a single user comment. It uses a structured Learning Engine:
- **Observation & Evidence**: Tracks successes, failures, and user corrections.
- **Confidence Scoring**: A behavior (e.g., "User prefers Chrome") is only promoted to persistent learning once enough evidence/confidence is gathered.
- **Decay**: Stale or failing preferences degrade over time.

### 2.4 Advanced Voice Subsystem
The voice pipeline is highly sophisticated, including:
- **VAD (Voice Activity Detection)**: Real-time noise tolerance.
- **Wake Word Learning**: Continuously evaluates false positives/negatives to train better local models.
- **Tone Analysis**: Analyzes pitch, volume, and speech rate to adapt TTS delivery.
- **Barge-In**: If the user speaks while Clovis is talking, TTS instantly pauses, the current response generation is cancelled, and the new utterance is processed.

---

## 3. GRACEFUL DEGRADATION

Clovis is designed to adapt to hardware limits and network availability. It supports multiple operating modes:
- `FULL`
- `LOW_RESOURCE` (Unloads heavy models, uses smaller fallbacks)
- `OFFLINE` (Falls back to deterministic functions and local-only models)
- `SAFE_MODE`

---

## 4. RELEASE GATES & TESTING PHILOSOPHY

A feature is considered incomplete until it has paths for: normal execution, timeout, cancellation, failure, verification, recovery, logging, and testing.

Clovis relies on strict Unit, Integration, Failure, and Cross-Platform testing before any module is considered production-ready.
