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
            import pyperclip
            pyperclip.copy(text)
            pyautogui.hotkey("ctrl", "v")
            ctx.say("Typed it for you, sir.")
        except Exception as e:
            log.error(f"Failed to type: {e}")
            ctx.say(f"I couldn't type that, sir.")

def _handle_generate_and_type(match: re.Match, ctx: Context) -> None:
    doc_type = match.groupdict().get("doc") or "text"
    topic = match.group("topic").strip()
    
    ctx.say(f"Drafting that for you now, sir.")
    try:
        from core.llm import generate_chat
        prompt = f"Write a {doc_type} about {topic}. Provide only the raw text, no conversational filler, no markdown formatting if possible."
        # Call LLM
        messages = [{"role": "user", "content": prompt}]
        response = generate_chat(messages)
        
        # Type the response using clipboard to support special characters
        import pyperclip
        pyperclip.copy(response)
        pyautogui.hotkey("ctrl", "v")
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
# Vision-driven screen interaction
#
# These handlers ground a described element with the vision engine instead of
# clicking wherever the cursor happens to be. They are registered *before* the
# blind click/type patterns below, because the old ``\b(click)\b`` pattern also
# matched "click on the Submit button" and turned it into a no-op click at the
# current cursor position.
# ---------------------------------------------------------------------------
def _handle_vision_click(match: re.Match, ctx: Context) -> None:
    target = (match.group("element") or "").strip(" .")
    if not target:
        ctx.say("What should I click, sir?")
        return

    from core.screen import click_element

    ctx.say(f"Looking for the {target}.")
    log.info("Vision click: %r", target)
    ok, message = click_element(target)
    if ok:
        ctx.say(f"Clicked the {target}.")
    else:
        log.warning("Vision click failed for %r: %s", target, message)
        ctx.say(f"I couldn't find the {target} on screen, sir.")


def _handle_vision_type(match: re.Match, ctx: Context) -> None:
    text = (match.group("text") or "").strip()
    element = (match.group("element") or "").strip(" .")
    if not text or not element:
        ctx.say("Tell me what to type and where, sir.")
        return

    from core.screen import type_into_element

    ctx.say(f"Finding the {element}.")
    log.info("Vision type: %r into %r", text, element)
    ok, message = type_into_element(element, text)
    if ok:
        ctx.say(f"Typed it into the {element}.")
    else:
        log.warning("Vision type failed for %r: %s", element, message)
        ctx.say(f"I couldn't find the {element}, sir.")


def _handle_focus_search(match: re.Match, ctx: Context) -> None:
    from core.screen import click_element

    ctx.say("Looking for the search bar.")
    ok, message = click_element(
        "the search input field where a user types a query")
    if ok:
        ctx.say("The search bar is ready, sir.")
    else:
        log.warning("Focus search failed: %s", message)
        ctx.say("I couldn't find a search bar on screen, sir.")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
PATTERNS = [
    # --- vision-first patterns (must precede the blind click/type ones) ----
    # "type hello into the search bar", "write I am late in the message box"
    (r"^(?:please\s+)?(?:type|write|enter|put)\s+(?P<text>.+?)\s+"
     r"(?:in|into|inside|on)\s+(?:the\s+|my\s+)?(?P<element>.+?)\s*$",
     _handle_vision_type),
    # "go to the search bar", "focus the search bar", "move to search"
    (r"^(?:please\s+)?(?:go\s+to|focus(?:\s+on)?|move\s+to|get\s+to)\s+"
     r"(?:the\s+|my\s+)?(?:search\s*(?:bar|box|field)?|search)\s*$",
     _handle_focus_search),
    # "click on the Submit button", "click the search bar", "tap the X icon"
    (r"^(?:please\s+)?(?:click|tap)\s+(?:on\s+|onto\s+)?(?:the\s+|my\s+)?"
     r"(?P<element>[A-Za-z0-9][^.!?]{0,60}?)\s*$",
     _handle_vision_click),
    # --- direct input -----------------------------------------------------
    (r"\b(?:move )?mouse (?P<dir>up|down|left|right)(?: by (?P<amount>\d+))?\b", _handle_move_mouse),
    (r"\b(?P<type>right click|double click|click)\b", _handle_click),
    (r"\b(?:generate and type|draft and type|write a(?:n)? (?P<doc>email|file|letter|paragraph|essay|story|script|code|message|poem) about|write about)\s+(?P<topic>.+)\b", _handle_generate_and_type),
    (r"\b(?:type|write)\s+(?P<text>.+)\b", _handle_type),
    (r"\b(?:press|hit)\s+(?P<key>enter|escape|esc|space|tab|backspace|delete|up|down|left|right)\b", _handle_press_key),
]

def register(router: Router) -> None:
    for pattern, handler in PATTERNS:
        router.register(pattern, handler)
