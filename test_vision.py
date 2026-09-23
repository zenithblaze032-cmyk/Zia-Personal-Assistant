import os
import re
import pyautogui
import google.generativeai as genai
from PIL import Image

def test_vision():
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("No API KEY")
        return
        
    genai.configure(api_key=api_key)
    filepath = "vision_click.png"
    pyautogui.screenshot().save(filepath)
    
    img = Image.open(filepath)
    model = genai.GenerativeModel('gemini-flash-latest') 
    
    prompt = "Return the bounding box for the 'Start Menu button'. Return only the bounding box in [ymin, xmin, ymax, xmax] format."
    print("Calling Gemini...")
    response = model.generate_content([img, prompt])
    text = response.text.strip()
    print("Gemini Output:", text)
    
    match = re.search(r'\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]', text)
    if not match:
        print("Failed to match regex.")
    else:
        print("Regex Matched!", match.groups())

if __name__ == "__main__":
    test_vision()
