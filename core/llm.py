import logging
import os
from typing import List, Dict, Any
import ollama
from core.tools import available_tools

# Cloud API Clients
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from google import genai
    if os.environ.get("GEMINI_API_KEY"):
        gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    else:
        gemini_client = None
except ImportError:
    genai = None
    gemini_client = None

log = logging.getLogger("Zia.llm")

CHAT_MODEL = "llama3.2:3b"
EMBEDDING_MODEL = "nomic-embed-text:latest"


def local_generate_chat(messages: List[Dict[str, Any]], use_tools: bool = True) -> str:
    """
    Generate a response from the local LLM using the provided message history.
    Messages should be a list of dicts with 'role' and 'content'.
    Supports tool calling if use_tools is True.
    """
    try:
        import datetime
        now = datetime.datetime.now()
        system_prompt = f"You are Zia, an AI assistant. The current date and time is {now.strftime('%Y-%m-%d %H:%M:%S')}."
        
        current_messages = list(messages)
        if not any(m.get('role') == 'system' for m in current_messages):
            current_messages.insert(0, {"role": "system", "content": system_prompt})

        
        # Build tool schemas for Ollama
        ollama_tools = []
        if use_tools:
            for func in available_tools:
                import inspect
                sig = inspect.signature(func)
                doc = inspect.getdoc(func) or ""
                
                properties = {}
                required = []
                for name, param in sig.parameters.items():
                    param_type = "string"
                    if param.annotation != inspect.Parameter.empty:
                        if param.annotation == int:
                            param_type = "integer"
                        elif param.annotation == bool:
                            param_type = "boolean"
                        elif param.annotation == float:
                            param_type = "number"
                    properties[name] = {"type": param_type, "description": f"Parameter {name}"}
                    if param.default == inspect.Parameter.empty:
                        required.append(name)
                        
                ollama_tools.append({
                    "type": "function",
                    "function": {
                        "name": func.__name__,
                        "description": doc,
                        "parameters": {
                            "type": "object",
                            "properties": properties,
                            "required": required
                        }
                    }
                })
            
        while True:
            chat_kwargs = {
                "model": CHAT_MODEL,
                "messages": current_messages
            }
            if use_tools and ollama_tools:
                chat_kwargs["tools"] = ollama_tools
                
            response = ollama.chat(**chat_kwargs)
            
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

def local_generate_vision_chat(prompt: str, image_bytes: bytes) -> str:
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


def build_openai_tools():
    import inspect
    tools = []
    for func in available_tools:
        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or ""
        properties = {}
        required = []
        for name, param in sig.parameters.items():
            param_type = "string"
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == float:
                    param_type = "number"
            properties[name] = {"type": param_type, "description": f"Parameter {name}"}
            if param.default == inspect.Parameter.empty:
                required.append(name)
                
        tools.append({
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": doc,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        })
    return tools

def call_openai_compatible(messages, use_tools, base_url, api_key, model_name):
    """Generic function to call an OpenAI-compatible API."""
    if not OpenAI:
        raise ImportError("openai package not installed")

    client = OpenAI(base_url=base_url, api_key=api_key)

    kwargs = {
        "model": model_name,
        "messages": messages,
    }

    tools = build_openai_tools() if use_tools else []
    if tools:
        kwargs["tools"] = tools

    response = client.chat.completions.create(**kwargs)
    message = response.choices[0].message

    if not message.tool_calls:
        return message.content or "Done."

    # Handle tool calls
    current_messages = list(messages)
    current_messages.append(message)

    for tool_call in message.tool_calls:
        tool_name = tool_call.function.name
        import json
        tool_args = json.loads(tool_call.function.arguments)

        tool_func = next(
            (t for t in available_tools if t.__name__ == tool_name), None)
        if tool_func:
            log.info(
                f"Hybrid API Executing tool: {tool_name} with args: {tool_args}")
            try:
                tool_result = tool_func(**tool_args)
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": str(tool_result)
                })
            except Exception as e:
                log.error(f"Error executing tool {tool_name}: {e}")
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": f"Error: {e}"
                })
        else:
            log.error(f"Tool {tool_name} not found")
            current_messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": f"Error: Tool not found"
            })

    # Send tool results back for a final answer
    final_response = client.chat.completions.create(
        model=model_name,
        messages=current_messages
    )
    return final_response.choices[0].message.content or "Done."


def call_gemini(messages, use_tools):
    if not genai or not gemini_client:
        raise ImportError("google-genai package not installed or client not configured")

    # Build tools for Gemini
    gemini_tools = []
    if use_tools:
        # We can just map our available_tools or let the google-genai SDK handle it 
        # (the SDK allows passing callables directly).
        gemini_tools = available_tools

    gemini_history = []
    for m in messages[:-1]:
        role = "user" if m["role"] in ["user", "system"] else "model"
        # The new SDK takes types.Content for history
        gemini_history.append(genai.types.Content(role=role, parts=[genai.types.Part.from_text(text=m["content"])]))

    chat = gemini_client.chats.create(
        model="gemini-1.5-flash",
        config=genai.types.GenerateContentConfig(
            tools=gemini_tools if gemini_tools else None
        )
    )
    # the new SDK chat does not accept history in the same way, let's just use generate_content
    # wait, instead of using chats.create with history, we can just use generate_content with contents array
    contents = []
    for m in messages:
        role = "user" if m["role"] in ["user", "system"] else "model"
        contents.append(genai.types.Content(role=role, parts=[genai.types.Part.from_text(m["content"])]))

    response = gemini_client.models.generate_content(
        model="gemini-1.5-flash",
        contents=contents,
        config=genai.types.GenerateContentConfig(
            tools=gemini_tools if gemini_tools else None
        )
    )
    return response.text


def call_gemini_vision(prompt: str, image_bytes: bytes) -> str:
    """Analyze an image with Gemini when a Cloud API key is available."""
    if not genai or not gemini_client:
        raise ImportError("google-genai package not installed or client not configured")

    image = Image.open(BytesIO(image_bytes))
    response = gemini_client.models.generate_content(
        model="gemini-1.5-flash",
        contents=[prompt, image]
    )
    return response.text or "I couldn't find anything useful on the screen."


def generate_vision_chat(prompt: str, image_bytes: bytes) -> str:
    """Use the fastest configured vision provider, starting with Hugging Face."""
    if hf_client:
        try:
            import base64
            b64_img = base64.b64encode(image_bytes).decode("utf-8")
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"},
                        },
                    ],
                }
            ]
            # Use Qwen2-VL for fast, highly capable vision
            response = hf_client.chat.completions.create(
                model="Qwen/Qwen2-VL-7B-Instruct",
                messages=messages,
                max_tokens=256
            )
            return response.choices[0].message.content or "I couldn't find anything useful on the screen."
        except Exception as exc:
            log.warning("API Fallback: Hugging Face vision failed - %s", exc)

    if os.environ.get("GEMINI_API_KEY") and genai:
        try:
            return call_gemini_vision(prompt, image_bytes)
        except Exception as exc:
            log.warning("API Fallback: Gemini vision failed - %s", exc)

    return local_generate_vision_chat(prompt, image_bytes)


def generate_chat(messages: List[Dict[str, Any]], use_tools: bool = True) -> str:
    """
    Hybrid API LLM generation. Attempts lightning-fast inference by cascading through APIs.
    Fallback order: Groq -> Gemini Flash -> OpenRouter -> Local.
    """
    import datetime
    now = datetime.datetime.now()
    system_prompt = f"You are Zia, an AI assistant in Hybrid API Mode. The current date and time is {now.strftime('%Y-%m-%d %H:%M:%S')}."

    current_messages = list(messages)
    if not any(m.get('role') == 'system' for m in current_messages):
        current_messages.insert(
            0, {"role": "system", "content": system_prompt})

    providers = [
        {
            "name": "HuggingFace",
            "func": call_openai_compatible,
            "args": {
                "base_url": "https://api-inference.huggingface.co/v1/",
                "api_key": os.environ.get("HUGGING_FACE_KEY"),
                "model_name": "Qwen/Qwen2.5-72B-Instruct" # Lightning fast HF model
            }
        },
        {
            "name": "Groq",
            "func": call_openai_compatible,
            "args": {
                "base_url": "https://api.groq.com/openai/v1",
                "api_key": os.environ.get("GROQ_API_KEY"),
                "model_name": "openai/gpt-oss-120b"
            }
        },
        {
            "name": "Gemini",
            "func": call_gemini,
            "args": {}
        },
        {
            "name": "OpenRouter",
            "func": call_openai_compatible,
            "args": {
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": os.environ.get("OPENROUTER_API_KEY"),
                "model_name": "meta-llama/llama-3.1-70b-instruct"
            }
        }
    ]

    for provider in providers:
        name = provider["name"]
        args = provider["args"]

        # Skip if missing API key
        if name != "Gemini" and not args.get("api_key"):
            continue
        if name == "Gemini" and not os.environ.get("GEMINI_API_KEY"):
            continue

        try:
            log.info(f"API Fallback: Attempting with {name}")
            if name == "Gemini":
                return provider["func"](current_messages, use_tools)
            else:
                return provider["func"](current_messages, use_tools, **args)
        except Exception as e:
            log.warning(f"API Fallback: {name} failed - {e}")
            continue

    # If we exhaust all providers, we fallback to local Ollama and use offline mode
    log.error(
        "API Fallback: All fast APIs failed or limits reached. Falling back to local.")
    

    # We trigger the speech warning via a side-effect or we just let it return the local chat
    from core.tts import say_text
    say_text('Network or API limit reached, falling back to local mode.')

    return local_generate_chat(messages, use_tools)
