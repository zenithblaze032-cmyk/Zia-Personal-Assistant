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
