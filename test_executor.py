import sys
import logging
from core.executor import AgentNovaExecutor

logging.basicConfig(level=logging.INFO)

exec_obj = AgentNovaExecutor()
print("Initialized executor.")

text = "Calculate 5 plus 5"
text_with_nlp = text + "\n[System NLP Analysis] Intent Root: CALCULATE | Extracted Subjects: 5 (CARDINAL)"

print("Sending to agent...")
res = exec_obj.execute(text_with_nlp)
print("Result:", res)
