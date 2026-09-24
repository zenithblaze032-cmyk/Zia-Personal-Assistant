import os
import ast
import operator
import re
import time
import requests
import pyautogui
from ddgs import DDGS
import logging

log = logging.getLogger("Zia.tools")

def search_web(query: str) -> str:
    """
    Search the web for real-time information, news, or answers.
    Use this when you need live information or don't know the answer.
    """
    try:
        from core.config import task_abort_event
        if task_abort_event.is_set(): return "Task aborted by user."
        results = DDGS().text(query, max_results=3)
        if not results:
            return "No results found."
        
        output = []
        for res in results:
            output.append(f"Title: {res['title']}\nSnippet: {res['body']}\nLink: {res['href']}")
        return "\n\n".join(output)
    except Exception as e:
        log.error(f"Search failed: {e}")
        return f"Error searching the web: {e}"

def read_file(path: str) -> str:
    """
    Read the contents of a file on the local file system.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(path: str, content: str) -> str:
    """
    Write or overwrite a file on the local file system.
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        if os.name == 'nt':
            os.startfile(path)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {e}"

def list_directory(path: str) -> str:
    """
    List all files and folders in a given directory path.
    """
    try:
        items = os.listdir(path)
        if os.name == 'nt':
            os.startfile(path)
        return "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {e}"

def calculate(expression: str) -> str:
    """
    Evaluate a mathematical expression.
    Supports basic arithmetic operators (+, -, *, /, **).
    """
    # Safe eval for basic math
    operators = {
        ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.BitXor: operator.xor,
        ast.USub: operator.neg
    }

    def eval_expr(expr):
        return eval_(ast.parse(expr, mode='eval').body)

    def eval_(node):
        if isinstance(node, ast.Constant): # Python 3.8+ Uses Constant instead of Num
            return node.value
        elif hasattr(ast, 'Num') and isinstance(node, ast.Num): 
            return node.n
        elif isinstance(node, ast.BinOp): # <left> <operator> <right>
            return operators[type(node.op)](eval_(node.left), eval_(node.right))
        elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
            return operators[type(node.op)](eval_(node.operand))
        else:
            raise TypeError(node)

    try:
        result = eval_expr(expression)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"

def fetch_webpage(url: str) -> str:
    """
    Fetches a webpage and extracts the raw readable text from the HTML using a headless browser.
    Use this to read articles, documentation, or any text-based website.
    
    Args:
        url: The full URL to fetch (e.g. "https://en.wikipedia.org/wiki/Quantum_mechanics")
    """
    try:
        from core.config import task_abort_event
        if task_abort_event.is_set(): return "Task aborted by user."
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            # Launch chromium in headless mode
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            
            # Wait until the network is mostly idle to ensure JS has loaded
            page.goto(url, wait_until='networkidle', timeout=15000)
            
            # Extract text specifically from the body
            text = page.locator("body").inner_text()
            
            browser.close()
            
        # Clean up excessive whitespace
        lines = (line.strip() for line in text.splitlines())
        text = '\n'.join(line for line in lines if line)
        
        # Return first 10,000 characters to prevent overwhelming the context window
        if len(text) > 10000:
            return text[:10000] + "\n... (Content truncated due to length)"
            
        return text
    except Exception as e:
        log.error(f"Failed to fetch webpage with Playwright: {e}")
        return f"Failed to fetch webpage: {e}"

def take_screenshot() -> str:
    """
    Takes a screenshot of the user's primary monitor and saves it to a temporary file.
    Returns the absolute path to the saved screenshot image file.
    """
    try:
        # Create a temp directory for screenshots if it doesn't exist
        import tempfile
        temp_dir = os.path.join(tempfile.gettempdir(), "zia_screenshots")
        os.makedirs(temp_dir, exist_ok=True)
        
        filename = f"screenshot_{int(time.time())}.png"
        filepath = os.path.join(temp_dir, filename)
        
        # Take the screenshot
        pyautogui.screenshot(filepath)
        
        return f"Screenshot saved successfully at: {filepath}"
    except Exception as e:
        return f"Failed to take screenshot: {e}"

def minimize_window(window_title: str) -> str:
    """
    Minimizes a window by its title. Use this to hide windows.
    Args:
        window_title: A substring of the window title to minimize.
    """
    try:
        import pygetwindow as gw
        windows = gw.getWindowsWithTitle(window_title)
        if not windows:
            return f"No window found matching title: {window_title}"
        for w in windows:
            w.minimize()
        return f"Successfully minimized windows matching '{window_title}'"
    except Exception as e:
        return f"Failed to minimize window: {e}"

def maximize_window(window_title: str) -> str:
    """
    Maximizes a window by its title. Use this to focus or expand windows.
    Args:
        window_title: A substring of the window title to maximize.
    """
    try:
        import pygetwindow as gw
        windows = gw.getWindowsWithTitle(window_title)
        if not windows:
            return f"No window found matching title: {window_title}"
        for w in windows:
            w.restore()
            w.maximize()
            try:
                w.activate()
            except:
                pass
        return f"Successfully maximized windows matching '{window_title}'"
    except Exception as e:
        return f"Failed to maximize window: {e}"

def press_keys(keys: str) -> str:
    """
    Presses a sequence of keyboard keys. Use this to send shortcuts like volumeup, volumedown, volumemute, playpause, win, enter.
    Args:
        keys: Comma-separated list of keys to press (e.g. 'volumemute', 'ctrl,c', 'win,d').
    """
    try:
        key_list = [k.strip() for k in keys.split(",")]
        pyautogui.hotkey(*key_list)
        return f"Successfully pressed keys: {keys}"
    except Exception as e:
        return f"Failed to press keys: {e}"

def click_on_screen(element_description: str) -> str:
    """
    Finds a UI element on the screen based on the description and clicks it using the mouse.
    Args:
        element_description: What to click on (e.g. 'Submit button', 'Search bar', 'X icon').
    """
    try:
        from core.screen import click_element
        ok, message = click_element(element_description)
        return message if ok else f"Failed: {message}"
    except Exception as e:
        return f"Error executing click_on_screen: {e}"


def _legacy_click_on_screen(element_description: str) -> str:
    """
    Finds a UI element on the screen based on the description and clicks it using the mouse.
    Args:
        element_description: What to click on (e.g. 'Submit button', 'Search bar', 'X icon').
    """
    try:
        import google.generativeai as genai
        from PIL import Image
        import tempfile

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key or api_key == "mock":
            return "Error: Valid GEMINI_API_KEY is not set."
            
        genai.configure(api_key=api_key)
        
        temp_dir = os.path.join(tempfile.gettempdir(), "zia_screenshots")
        os.makedirs(temp_dir, exist_ok=True)
        filepath = os.path.join(temp_dir, "vision_click.png")
        
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        
        img = Image.open(filepath)
        model = genai.GenerativeModel('gemini-flash-latest') 
        
        prompt = f"Return the bounding box for the '{element_description}'. Return only the bounding box in [ymin, xmin, ymax, xmax] format."
        
        response = model.generate_content([img, prompt])
        text = response.text.strip()
        
        # Match array even if there are newlines between numbers
        match = re.search(r'\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]', text)
        if not match:
            return f"Failed to find element. Vision model returned: {text}"
            
        ymin, xmin, ymax, xmax = map(int, match.groups())
        
        screen_w, screen_h = pyautogui.size()
        center_x_norm = (xmin + xmax) / 2
        center_y_norm = (ymin + ymax) / 2
        
        click_x = int((center_x_norm / 1000) * screen_w)
        click_y = int((center_y_norm / 1000) * screen_h)
        
        pyautogui.moveTo(click_x, click_y, duration=0.2)
        pyautogui.click()
        
        return f"Clicked on {element_description} at coordinates ({click_x}, {click_y})."
    except Exception as e:
        return f"Error executing click_on_screen: {e}"

def type_on_screen(element_description: str, text: str) -> str:
    """
    Finds a text field on the screen based on the description, clicks it, and types the text.
    Args:
        element_description: The text box to find (e.g. 'Search bar', 'Chat input').
        text: The text to type into the box.
    """
    try:
        from core.screen import type_into_element
        ok, message = type_into_element(element_description, text)
        return message if ok else f"Failed: {message}"
    except Exception as e:
        return f"Error executing type_on_screen: {e}"


def _legacy_type_on_screen(element_description: str, text: str) -> str:
    """
    Finds a text field on the screen based on the description, clicks it, and types the text.
    Args:
        element_description: The text box to find (e.g. 'Search bar', 'Chat input').
        text: The text to type into the box.
    """
    click_res = _legacy_click_on_screen(element_description)
    if "Error" in click_res or "Failed" in click_res:
        return click_res
        
    pyautogui.write(text, interval=0.01)
    return f"Typed '{text}' into {element_description}."

# Expose available tools for ollama (SIMPLE chat model)
available_tools = [
    search_web,
    read_file,
    write_file,
    list_directory,
    calculate,
    fetch_webpage,
    take_screenshot,
    minimize_window,
    maximize_window,
    press_keys,
    click_on_screen,
    type_on_screen
]
