import os
import ast
import operator
import re
import time
import requests
import pyautogui
from duckduckgo_search import DDGS
import logging

log = logging.getLogger("Zia.tools")

def search_web(query: str) -> str:
    """
    Search the web for real-time information, news, or answers.
    Use this when you need live information or don't know the answer.
    """
    try:
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
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {e}"

def list_directory(path: str) -> str:
    """
    List all files and folders in a given directory path.
    """
    try:
        items = os.listdir(path)
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
    Fetches a webpage and extracts the raw readable text from the HTML.
    Use this to read articles, documentation, or any text-based website.
    
    Args:
        url: The full URL to fetch (e.g. "https://en.wikipedia.org/wiki/Quantum_mechanics")
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Simple HTML stripping since BeautifulSoup is not guaranteed to be installed
        html = response.text
        
        # Remove script and style elements
        html = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Return first 10,000 characters to prevent overwhelming the context window
        if len(text) > 10000:
            return text[:10000] + "\n... (Content truncated due to length)"
            
        return text
    except Exception as e:
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
    press_keys
]
