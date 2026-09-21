import logging
from typing import List, Dict, Any
import ollama
from core.tools import available_tools

log = logging.getLogger("Zia.llm")

CHAT_MODEL = "llama3.2:3b"
EMBEDDING_MODEL = "nomic-embed-text:latest"


def generate_chat(messages: List[Dict[str, Any]]) -> str:
    """
    Generate a response from the local LLM using the provided message history.
    Messages should be a list of dicts with 'role' and 'content'.
    Supports tool calling.
    """
    try:
        current_messages = list(messages)
        
        while True:
            response = ollama.chat(
                model=CHAT_MODEL,
                messages=current_messages,
                tools=available_tools
            )
            
            message = response['message']
            current_messages.append(message)
            
            if not message.get('tool_calls'):
                return message['content'] or "Done."
                
            for tool_call in message['tool_calls']:
                tool_name = tool_call['function']['name']
                tool_args = tool_call['function']['arguments']
                
                tool_func = next((t for t in available_tools if t.__name__ == tool_name), None)
                if tool_func:
                    log.info(f"Executing tool: {tool_name} with args: {tool_args}")
                    try:
                        tool_result = tool_func(**tool_args)
                        current_messages.append({
                            'role': 'tool',
                            'name': tool_name,
                            'content': str(tool_result)
                        })
                    except Exception as e:
                        log.error(f"Error executing tool {tool_name}: {e}")
                        current_messages.append({
                            'role': 'tool',
                            'name': tool_name,
                            'content': f"Error: {e}"
                        })
                else:
                    log.error(f"Tool {tool_name} not found")
                    current_messages.append({
                        'role': 'tool',
                        'name': tool_name,
                        'content': f"Error: Tool {tool_name} not found"
                    })
                    
    except Exception as e:
        log.error(f"Error communicating with local LLM ({CHAT_MODEL}): {e}")
        return "I'm having trouble connecting to my brain right now, sir."


VISION_MODEL = "moondream:latest"

def generate_vision_chat(prompt: str, image_bytes: bytes) -> str:
    """
    Generate a response from the local Vision LLM based on an image and a prompt.
    """
    try:
        response = ollama.chat(
            model=VISION_MODEL,
            messages=[{
                "role": "user",
                "content": prompt,
                "images": [image_bytes]
            }]
        )
        return response['message']['content']
    except Exception as e:
        log.error(f"Error communicating with local Vision LLM ({VISION_MODEL}): {e}")
        return "I couldn't analyze the screen, sir."


def generate_embedding(text: str) -> List[float]:
    """
    Generate an embedding vector for the given text.
    """
    try:
        response = ollama.embeddings(
            model=EMBEDDING_MODEL,
            prompt=text
        )
        return response['embedding']
    except Exception as e:
        log.error(f"Error generating embedding with {EMBEDDING_MODEL}: {e}")
        return []


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a batch of texts.
    (Ollama doesn't currently support true batching in its Python library for embeddings, 
     so we process them sequentially for now).
    """
    embeddings = []
    for text in texts:
        embeddings.append(generate_embedding(text))
    return embeddings
