import logging
import agentkthx.core.helpers
agentkthx.core.helpers.ALLOWED_PATH_PATTERNS.update(["C:\\", "D:\\", "E:\\", "F:\\", "/"])

from core.executor import AgentNovaExecutor

logging.basicConfig(level=logging.DEBUG)

executor = AgentNovaExecutor()
text = "create a new text file on my documents called test.txt and write hello world inside it"

print("Sending to agent...")
res = executor.agent.run(text)
if hasattr(res, "steps"):
    for s in res.steps:
        print("Tool call:", getattr(s, "tool_call", None))
        print("Tool result:", getattr(s, "tool_result", None))
        print("Error:", getattr(s, "error", None))
        break
