import os
import ast
import operator
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

# Expose available tools for ollama
available_tools = [
    search_web,
    read_file,
    write_file,
    list_directory,
    calculate
]
