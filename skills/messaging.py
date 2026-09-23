import re
import logging
import os
import time
import pyautogui
import speech_recognition as sr
from core.context import Context
from core.tools import type_on_screen

log = logging.getLogger("Zia.skills.messaging")

def _handle_message(match: re.Match, ctx: Context) -> None:
    full = match.group("full_command")
    
    # Try to split by keywords
    split_match = re.search(r'^(.*?)\s+(saying|that|to)\s+(.+)$', full, re.IGNORECASE)
    if split_match:
        person = split_match.group(1)
        message = split_match.group(3)
    else:
        # No keyword, assume first word is the person
        words = full.split()
        if len(words) > 1:
            person = words[0]
            message = " ".join(words[1:])
        else:
            person = full
            message = ""
            
    if not message:
        ctx.say("I didn't catch the message you wanted to send.")
        return
        
    ctx.say(f"Opening chat with {person}.")
    
    # Launch WhatsApp Web or focus existing window
    import webbrowser
    import pygetwindow as gw
    
    windows = gw.getWindowsWithTitle("WhatsApp")
    if windows:
        w = windows[0]
        try:
            w.restore()
            w.activate()
        except Exception:
            pass
        time.sleep(1.5) # Short wait to bring to foreground
    else:
        webbrowser.open("https://web.whatsapp.com/")
        time.sleep(10) # Wait for browser and WhatsApp Web to load
    
    # 1. Use Vision to click the search bar and type the person's name
    # We use a very specific description so Gemini doesn't confuse it with the browser's URL bar
    search_res = type_on_screen("WhatsApp chat search bar", person)
    if "Error" in search_res or "Failed" in search_res:
        log.error(f"Vision failed for search bar: {search_res}")
        ctx.say("I couldn't find the search bar on screen.")
        return
        
    time.sleep(1.5)
    pyautogui.press("enter")
    time.sleep(1)
    
    # 2. Use Vision to click the message input field and type the message
    msg_res = type_on_screen("WhatsApp type a message box at the bottom", message)
    if "Error" in msg_res or "Failed" in msg_res:
        log.error(f"Vision failed for message field: {msg_res}")
        ctx.say("I couldn't find the message box.")
        return
    
    # 3. Synchronous Voice Confirmation
    ctx.say("The message is ready. Should I send it?")
    
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            # Short listen for yes/no
            audio = recognizer.listen(source, timeout=7, phrase_time_limit=5)
            response = recognizer.recognize_google(audio).lower()
            
            if "yes" in response or "send" in response or "yeah" in response or "do it" in response:
                pyautogui.press("enter")
                ctx.say("Message sent.")
            else:
                ctx.say("Okay, I will not send it.")
        except sr.WaitTimeoutError:
            ctx.say("I didn't hear a confirmation, so I won't send it.")
        except Exception as e:
            log.error(f"Error during confirmation: {e}")
            ctx.say("I couldn't hear you clearly, message cancelled.")

def register(router) -> None:
    # Example: "message Ayush saying I will be late" or "text Ayush that I am coming"
    pattern = r"(?i)\b(?:message|text|whatsapp)\s+(?P<full_command>.+)"
    router.register(pattern, _handle_message)
