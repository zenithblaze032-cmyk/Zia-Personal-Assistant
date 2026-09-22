# Zia Upgrade Testing Procedure

Follow these steps to manually verify Zia's subsystems after any codebase upgrade.

## 1. Wake & Basic STT
- **Action**: Say "Wake up Zia"
- **Expected**: Zia wakes up and responds "Welcome back sir, how can I help you?".

## 2. Fast Regex Skills (Bypass LLM)
- **Action**: Say "Take a screenshot"
- **Expected**: Takes a screenshot immediately and saves it to the Pictures folder without hitting the LLM.

## 3. RAG Memory & Simple LLM Routing
- **Action**: Say "Remember that the secret code is 42."
- **Expected**: Zia acknowledges "Note saved" and writes the embedding to `memory.db`.
- **Action**: Say "What is the secret code?"
- **Expected**: EffGen classifies the intent as `SIMPLE`, injects the RAG memory into the context, and the local LLM answers "42".

## 4. Complex Tool Execution (AgentNova)
- **Action**: Say "List the files in my documents folder"
- **Expected**: EffGen classifies as `MULTI_STEP` or `TOOL`. AgentNova intercepts it, uses the `list_directory` tool, and reads the contents back.

## 5. Safety State Machine
- **Action**: Say "Delete the temp files"
- **Expected**: AgentNova Executor flags the dangerous keyword (`delete`) and halts execution, saying "Please manually confirm by saying 'proceed' before I continue."
- **Action**: Say "proceed"
- **Expected**: The state machine catches the confirmation and AgentNova executes the deletion.
- **Action (Alternative)**: Say "cancel"
- **Expected**: The state machine resets and aborts the operation.

## 6. Headless Web Browsing (Phase 2)
- **Action**: Say "Search Wikipedia for Quantum Computing, read the article, and give me a short summary."
- **Expected**: AgentNova chains `web-search` with `fetch_webpage` to download the HTML, strip tags, and generate a summary for TTS playback.

## 7. Deep OS & System Integration (Phase 3)
- **Action**: Say "Maximize the Notepad window" or "Minimize my browser."
- **Expected**: AgentNova uses `maximize_window` or `minimize_window` from `pygetwindow` to adjust the window state.
- **Action**: Say "Mute my volume."
- **Expected**: AgentNova uses the `press_keys` tool to send the `volumemute` hotkey via `pyautogui`.

## 8. Proactive Memory Consolidation (Phase 4)
- **Action**: Tell Zia a personal fact, wait for her reply, then say "Go to sleep."
- **Expected**: Zia enters the `ASLEEP` state. In the background, the console logs should show the `consolidate_memory` agent waking up, running the LLM against the short-term transcript, and extracting the fact to the RAG database (`Saved to LTM: ...`).
