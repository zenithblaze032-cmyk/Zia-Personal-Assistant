import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

print("====================================================")
print("             ZEN MODE API DIAGNOSTICS               ")
print("====================================================\n")

def test_openai_compatible(name, base_url, api_key, model_name):
    if not api_key or api_key == "mock":
        print(f"[\u274C] {name} SKIPPED: Missing API Key in .env")
        return
    
    if not OpenAI:
        print(f"[\u274C] {name} SKIPPED: openai python package not installed")
        return
        
    print(f"[*] Testing {name} with model: {model_name}...")
    client = OpenAI(base_url=base_url, api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Hello, this is a quick test. Reply exactly with 'OK'."}],
            max_tokens=10
        )
        msg = response.choices[0].message.content.strip()
        print(f"[\u2705] {name} SUCCESS! Response: {msg}")
    except Exception as e:
        print(f"[\u274C] {name} FAILED: {e}")

def test_gemini():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "mock":
        print("[\u274C] Gemini SKIPPED: Missing API Key in .env")
        return
        
    if not genai:
        print("[\u274C] Gemini SKIPPED: google-generativeai python package not installed")
        return
        
    print("[*] Testing Gemini with model: gemini-1.5-flash...")
    try:
        genai.configure(api_key=api_key)
        # Testing the standard and most stable gemini string
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content("Hello, this is a quick test. Reply exactly with 'OK'.")
        print(f"[\u2705] Gemini SUCCESS! Response: {response.text.strip()}")
    except Exception as e:
        print(f"[\u274C] Gemini FAILED: {e}")

# Run tests
test_openai_compatible(
    "Groq", 
    "https://api.groq.com/openai/v1", 
    os.environ.get("GROQ_API_KEY"), 
    "openai/gpt-oss-120b" # Updated to their newest active model
)
print("")

test_gemini()
print("")

test_openai_compatible(
    "OpenRouter", 
    "https://openrouter.ai/api/v1", 
    os.environ.get("OPENROUTER_API_KEY"), 
    "meta-llama/llama-3.1-70b-instruct"
)

print("\n====================================================")
print("Diagnostics Complete.")
