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
                    system_prompt="You are Zia, an autonomous local agent. Fulfill the user's task."
                )
            except ImportError:
                self.agent = None
        else:
            self.agent = None

    def execute(self, text: str) -> str:
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

        log.info(f"Executing complex task via AgentNova: {text}")
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                # We submit the blocking run method to the pool
                future = pool.submit(self.agent.run, text)
                try:
                    result = future.result(timeout=AGENTNOVA_TIMEOUT_SEC)
                    # Attempt to extract response
                    if hasattr(result, "response"):
                        return result.response
                    elif hasattr(result, "content"):
                        return result.content
                    return str(result)
                except concurrent.futures.TimeoutError:
                    return f"The task took longer than {AGENTNOVA_TIMEOUT_SEC} seconds and was aborted."
        except Exception as e:
            log.error(f"AgentNova execution failed: {e}")
            return "I encountered an error while executing that task."
