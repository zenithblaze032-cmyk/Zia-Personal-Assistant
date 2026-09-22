import logging
import time
import concurrent.futures
from core.config import USE_AGENTNOVA, AGENTNOVA_CONFIRM_DANGEROUS, AGENTNOVA_TIMEOUT_SEC

log = logging.getLogger("Zia.executor")

class AgentNovaExecutor:
    def __init__(self):
        self.pending_command = None
        if USE_AGENTNOVA:
            try:
                import agentkthx
                # Initializing agent with shell and standard tools
                self.agent = agentkthx.Agent(
                    model="llama3.2:3b",
                    tools=["shell", "read_file", "write_file", "list_directory", "web-search"],
                    system_prompt=(
                        "You are Zia, an autonomous local agent on a WINDOWS machine.\n"
                        "The user's Desktop path is: \"C:\\Users\\Ayush Kumar\\Desktop\"\n"
                        "The user's Documents path is: \"C:\\Users\\Ayush Kumar\\Documents\"\n"
                        "IMPORTANT: Always wrap file paths in quotes (e.g. \"C:\\path\\to\\file\") when using the shell tool.\n"
                        "IMPORTANT: When using the `shell` tool, the argument name MUST be 'command' (not 'body').\n"
                        "If built-in file tools return security errors, fallback to using the `shell` tool with Windows CMD/PowerShell commands (e.g. `dir`, `type`).\n"
                        "CRITICAL: When using a tool, you MUST output ONLY the exact tool call format required. Do NOT include any conversational text like 'I will now run...' before the tool call."
                    )
                )
            except ImportError:
                self.agent = None
        else:
            self.agent = None

    def execute(self, text: str, ctx_memory=None) -> str:
        if not self.agent:
            return "My advanced execution module is offline, sir."

        # Safety Check - Confirmation state machine
        if self.pending_command and text.lower().strip() in ["proceed", "yes", "confirm", "do it"]:
            text = self.pending_command
            self.pending_command = None
        elif self.pending_command and text.lower().strip() in ["cancel", "no", "stop", "abort"]:
            self.pending_command = None
            return "Operation cancelled."
            
        if AGENTNOVA_CONFIRM_DANGEROUS and not self.pending_command:
            dangerous_keywords = ["delete", "remove", "rm ", "format ", "kill "]
            if any(k in text.lower() for k in dangerous_keywords):
                self.pending_command = text
                return "That sounds like a dangerous operation. Please manually confirm by saying 'proceed' before I continue."

        # Unify memory context
        if ctx_memory and hasattr(ctx_memory, "messages") and len(ctx_memory.messages) > 0:
            recent_context = []
            for msg in ctx_memory.messages:
                role = "User" if msg.get("role") == "user" else "Zia"
                recent_context.append(f"{role}: {msg.get('content')}")
            if recent_context:
                context_str = "\n".join(recent_context)
                # Keep logging clean, but modify the actual text sent to agent
                log.info(f"Executing complex task via AgentNova (with {len(recent_context)} prior messages context): {text}")
                text = f"Here is the recent conversation context:\n{context_str}\n\nUser's new request:\n{text}"
        else:
            log.info(f"Executing complex task via AgentNova: {text}")
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                # We submit the blocking run method to the pool
                future = pool.submit(self.agent.run, text)
                try:
                    result = future.result(timeout=AGENTNOVA_TIMEOUT_SEC)
                    # Safely handle AgentRun objects to prevent raw string dumps to TTS
                    if type(result).__name__ == "AgentRun":
                        if getattr(result, "final_answer", None):
                            return str(result.final_answer)
                        elif getattr(result, "success", True) is False:
                            return "I attempted the task, but I encountered a tool execution error and could not complete it."
                        else:
                            return "I have finished the task, sir."
                            
                    # Fallbacks for other generic return types
                    if hasattr(result, "response") and result.response:
                        return str(result.response)
                    elif hasattr(result, "content") and result.content:
                        return str(result.content)
                    return str(result)
                except concurrent.futures.TimeoutError:
                    return f"The task took longer than {AGENTNOVA_TIMEOUT_SEC} seconds and was aborted."
        except Exception as e:
            log.error(f"AgentNova execution failed: {e}")
            return "I encountered an error while executing that task."
