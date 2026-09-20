from __future__ import annotations

import logging
import re
import os
from typing import TYPE_CHECKING
import pyautogui

if TYPE_CHECKING:
    from core.context import Context
    from core.router import Router

log = logging.getLogger("Zia.skills.automation")

# Safety setting for pyautogui
pyautogui.FAILSAFE = False

# ---------------------------------------------------------------------------
# Mouse Handlers
# ---------------------------------------------------------------------------
def _handle_move_mouse(match: re.Match, ctx: Context) -> None:
    direction = match.group("dir").lower()
    amount_str = match.group("amount")
    
    amount = 100
    if amount_str:
        try:
            amount = int(amount_str)
        except ValueError:
            pass
            
    try:
        if direction == "up":
            pyautogui.move(0, -amount)
        elif direction == "down":
            pyautogui.move(0, amount)
        elif direction == "left":
            pyautogui.move(-amount, 0)
        elif direction == "right":
            pyautogui.move(amount, 0)
        ctx.say(f"Moved mouse {direction}.")
    except Exception as e:
        log.error(f"Failed to move mouse: {e}")
        ctx.say("I couldn't move the mouse, sir.")

def _handle_click(match: re.Match, ctx: Context) -> None:
    click_type = match.group("type").lower().strip() if match.group("type") else "click"
    try:
        if "double" in click_type:
            pyautogui.doubleClick()
            ctx.say("Double clicked.")
        elif "right" in click_type:
            pyautogui.rightClick()
            ctx.say("Right clicked.")
        else:
            pyautogui.click()
            ctx.say("Clicked.")
    except Exception as e:
        log.error(f"Failed to click: {e}")
        ctx.say("I couldn't click, sir.")

# ---------------------------------------------------------------------------
# Keyboard Handlers
# ---------------------------------------------------------------------------
def _handle_type(match: re.Match, ctx: Context) -> None:
    text = match.group("text").strip()
    if text:
        try:
            pyautogui.write(text, interval=0.01)
            ctx.say("Typed it for you, sir.")
        except Exception as e:
            log.error(f"Failed to type: {e}")
            ctx.say(f"I couldn't type that, sir.")

def _handle_generate_and_type(match: re.Match, ctx: Context) -> None:
    doc_type = match.groupdict().get("doc", "text")
    topic = match.group("topic").strip()
    
    ctx.say(f"Drafting that for you now, sir.")
    try:
        from core.llm import generate_chat
        prompt = f"Write a {doc_type} about {topic}. Provide only the raw text, no conversational filler, no markdown formatting if possible."
        # Call LLM
        messages = [{"role": "user", "content": prompt}]
        response = generate_chat(messages)
        
        # Type the response
        pyautogui.write(response, interval=0.01)
        log.info("Successfully generated and typed text.")
    except Exception as e:
        log.error(f"Failed to generate and type: {e}")
        ctx.say("I couldn't generate that text, sir.")

def _handle_press_key(match: re.Match, ctx: Context) -> None:
    key = match.group("key").lower().strip()
    
    # Map common spoken words to pyautogui keys
    key_map = {
        "enter": "enter",
        "return": "enter",
        "escape": "esc",
        "esc": "esc",
        "space": "space",
        "tab": "tab",
        "backspace": "backspace",
        "delete": "delete",
        "up": "up",
        "down": "down",
        "left": "left",
        "right": "right"
    }
    
    if key in key_map:
        try:
            pyautogui.press(key_map[key])
            ctx.say(f"Pressed {key}.")
        except Exception as e:
            log.error(f"Failed to press key: {e}")
            ctx.say("I couldn't press that key, sir.")
    else:
        ctx.say(f"I don't know how to press the {key} key.")

# ---------------------------------------------------------------------------
# File/App Open Handlers
# ---------------------------------------------------------------------------
def _handle_open(match: re.Match, ctx: Context) -> None:
    target = match.group("target").strip()
    try:
        # If it's a known shortname, expand it
        known_apps = {
            "calculator": "calc.exe",
            "notepad": "notepad.exe",
            "cmd": "cmd.exe",
            "command prompt": "cmd.exe",
            "explorer": "explorer.exe",
            "documents": "explorer.exe ::{450D8FBA-AD25-11D0-98A8-0800361B1103}"
        }
        
        launch_target = known_apps.get(target.lower(), target)
        
        import os
        os.startfile(launch_target)
        ctx.say(f"Opening {target}.")
    except FileNotFoundError:
        ctx.say(f"I couldn't find {target}, sir.")
    except Exception as e:
        log.error(f"Failed to open {target}: {e}")
        ctx.say(f"I couldn't open {target}, sir.")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
PATTERNS = [
    (r"\bmove mouse (?P<dir>up|down|left|right)(?: by (?P<amount>\d+))?\b", _handle_move_mouse),
    (r"\b(?P<type>right click|double click|click)\b", _handle_click),
    (r"\b(?:generate and type|draft and type|write a(?:n)? (?P<doc>email|file|letter|paragraph|essay|story|script|code|message|poem) about|write about)\s+(?P<topic>.+)\b", _handle_generate_and_type),
    (r"\b(?:type|write)\s+(?P<text>.+)\b", _handle_type),
    (r"\b(?:press|hit)\s+(?P<key>enter|escape|esc|space|tab|backspace|delete|up|down|left|right)\b", _handle_press_key),
    (r"\bopen\s+(?P<target>.+)\b", _handle_open),
]

def register(router: Router) -> None:
    for pattern, handler in PATTERNS:
        router.register(pattern, handler)
