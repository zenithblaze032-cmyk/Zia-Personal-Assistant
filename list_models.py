import os
import requests
from dotenv import load_dotenv
try:
    from google import genai
except ImportError:
    genai = None

load_dotenv()


def print_models(name, base_url, api_key):
    print(f"\n--- {name} Models ---")
    if not api_key or api_key == "mock":
        print("Missing API key.")
        return

    url = f"{base_url}/models"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            models = data.get("data", [])
            for m in models:
                print(m.get("id", "Unknown"))
        else:
            print(
                f"Failed to fetch models: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")


def print_gemini_models():
    print(f"\n--- Gemini Models ---")
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "mock":
        print("Missing API key.")
        return

    try:
        client = genai.Client(api_key=api_key)
        models = client.models.list()
        for m in models:
            print(m.name)
    except Exception as e:
        print(f"Error: {e}")


print_models("Groq", "https://api.groq.com/openai/v1",
             os.environ.get("GROQ_API_KEY"))
print_gemini_models()
