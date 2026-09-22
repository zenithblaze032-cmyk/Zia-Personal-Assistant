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
                from agentkthx import Tool, ToolParam, make_builtin_registry
                from core.tools import fetch_webpage, take_screenshot, minimize_window, maximize_window, press_keys
                
                fetch_webpage_tool = Tool(
                    name="fetch_webpage",
                    description="Fetches a webpage and extracts the raw readable text from the HTML.",
                    params=[ToolParam(name="url", type="string", description="The full URL to fetch")],
                    handler=fetch_webpage
                )
                take_screenshot_tool = Tool(
                    name="take_screenshot",
                    description="Takes a screenshot of the user's primary monitor and saves it to a temporary file.",
                    params=[],
                    handler=take_screenshot
                )
                minimize_window_tool = Tool(
                    name="minimize_window",
                    description="Minimizes a window by its title to hide it.",
                    params=[ToolParam(name="window_title", type="string", description="A substring of the window title to minimize")],
                    handler=minimize_window
                )
                maximize_window_tool = Tool(
                    name="maximize_window",
                    description="Maximizes or focuses a window by its title.",
                    params=[ToolParam(name="window_title", type="string", description="A substring of the window title to maximize")],
                    handler=maximize_window
                )
                press_keys_tool = Tool(
                    name="press_keys",
                    description="Presses a sequence of keyboard keys. Use for volume (volumemute, volumeup, volumedown), media (playpause), or shortcuts.",
                    params=[ToolParam(name="keys", type="string", description="Comma-separated list of keys to press")],
                    handler=press_keys
                )
                
                # Combine builtin tools and custom tools into a ToolRegistry
                registry = make_builtin_registry().subset(["shell", "read_file", "write_file", "list_directory", "web-search"])
                if hasattr(registry, "register_tool"):
                    registry.register_tool(fetch_webpage_tool)
                    registry.register_tool(take_screenshot_tool)
                    registry.register_tool(minimize_window_tool)
                    registry.register_tool(maximize_window_tool)
                    registry.register_tool(press_keys_tool)
                else:
                    registry.register(fetch_webpage_tool)
                    registry.register(take_screenshot_tool)
                    registry.register(minimize_window_tool)
                    registry.register(maximize_window_tool)
                    registry.register(press_keys_tool)
                
                # Initializing agent with shell and standard tools
                self.agent = agentkthx.Agent(
                    model="llama3.2:3b",
                    tools=registry,
                    system_prompt=(
                        "You are Zia, an autonomous local agent on a WINDOWS machine.\n"
                        "The user's Desktop path is: \"C:\\Users\\Ayush Kumar\\Desktop\"\n"
                        "The user's Documents path is: \"C:\\Users\\Ayush Kumar\\Documents\"\n"
                        "IMPORTANT: Always wrap file paths in quotes (e.g. \"C:\\path\\to\\file\") when using the shell tool.\n"
                        "IMPORTANT: When using the `shell` tool, the argument name MUST be 'command' (not 'body').\n"
                        "CRITICAL: For web searches or reading articles, you MUST use the `web-search` and `fetch_webpage` tools. NEVER use the `shell` tool to browse the internet.\n"
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
