import os
import logging
from io import BytesIO
from typing import List, Dict, Any
from PIL import Image
from core.tools import available_tools
from core.llm import generate_chat as local_generate_chat
from core.llm import generate_vision_chat as local_generate_vision_chat
from core.state import st

log = logging.getLogger("Zia.zen")

# We use the standard OpenAI client for Groq and OpenRouter.
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Attempt to configure Gemini if available
if genai and os.environ.get("GEMINI_API_KEY"):
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))


def build_openai_tools():
    """Builds the tool schema for OpenAI-compatible endpoints."""
    openai_tools = []
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
            properties[name] = {"type": param_type,
                                "description": f"Parameter {name}"}
            if param.default == inspect.Parameter.empty:
                required.append(name)

        openai_tools.append({
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
    return openai_tools


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
                f"Zen Mode Executing tool: {tool_name} with args: {tool_args}")
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
    if not genai:
        raise ImportError("google-generativeai package not installed")

    # Let's try the safest string for Gemini
    model = genai.GenerativeModel(
        'gemini-flash-latest', tools=available_tools if use_tools else None)

    # Very basic message conversion for Gemini (can be improved)
    gemini_history = []
    for m in messages:
        role = "user" if m["role"] in ["user", "system"] else "model"
        gemini_history.append({"role": role, "parts": [m["content"]]})

    chat = model.start_chat(history=gemini_history[:-1])
    response = chat.send_message(messages[-1]["content"])
    return response.text


def call_gemini_vision(prompt: str, image_bytes: bytes) -> str:
    """Analyze an image with Gemini when a Zen API key is available."""
    if not genai:
        raise ImportError("google-generativeai package not installed")

    model = genai.GenerativeModel("gemini-flash-latest")
    image = Image.open(BytesIO(image_bytes))
    response = model.generate_content([prompt, image])
    return response.text or "I couldn't find anything useful on the screen."


def generate_zen_vision(prompt: str, image_bytes: bytes) -> str:
    """Use the fastest configured vision provider, then the local vision model."""
    if os.environ.get("GEMINI_API_KEY") and genai:
        try:
            return call_gemini_vision(prompt, image_bytes)
        except Exception as exc:
            log.warning("Zen Mode: Gemini vision failed - %s", exc)

    return local_generate_vision_chat(prompt, image_bytes)


def generate_zen_chat(messages: List[Dict[str, Any]], use_tools: bool = True) -> str:
    """
    Zen Mode LLM generation. Attempts lightning-fast inference by cascading through APIs.
    Fallback order: Groq -> Gemini Flash -> OpenRouter -> Local.
    """
    import datetime
    now = datetime.datetime.now()
    system_prompt = f"You are Zia, an AI assistant in ZEN MODE (Lightning Speed). The current date and time is {now.strftime('%Y-%m-%d %H:%M:%S')}."

    current_messages = list(messages)
    if not any(m.get('role') == 'system' for m in current_messages):
        current_messages.insert(
            0, {"role": "system", "content": system_prompt})

    providers = [
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
            log.info(f"Zen Mode: Attempting with {name}")
            if name == "Gemini":
                return provider["func"](current_messages, use_tools)
            else:
                return provider["func"](current_messages, use_tools, **args)
        except Exception as e:
            log.warning(f"Zen Mode: {name} failed - {e}")
            continue

    # If we exhaust all providers, we fallback to local Ollama and disable Zen Mode
    log.error(
        "Zen Mode: All fast APIs failed or limits reached. Falling back to local.")
    st.zen_mode = False

    # We trigger the speech warning via a side-effect or we just let it return the local chat
    from core.tts import say_text
    from core.config import Zia_ZEN_OFF_PHRASE
    say_text(Zia_ZEN_OFF_PHRASE)

    return local_generate_chat(messages, use_tools)
