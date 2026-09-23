import sys
import os
sys.path.append(r"d:\Development\Zia")

# Mock the ollama/api keys things if they throw errors
os.environ["GROQ_API_KEY"] = "mock"
os.environ["OPENROUTER_API_KEY"] = "mock"
os.environ["GEMINI_API_KEY"] = "mock"

try:
    from core.router import Router
    import skills

    router = Router()
    skills.register_all(router)

    with open(r"d:\Development\Zia\capabilities_dump.txt", "w", encoding="utf-8") as f:
        f.write("=== REGEX ROUTES ===\n")
        for pattern, handler in router._routes:
            f.write(
                f"Pattern: {pattern.pattern}\nHandler: {handler.__doc__ or handler.__name__}\n\n")

        f.write("\n=== INTENT ROUTES ===\n")
        # Since intents are just vectors, let's just list the handlers
        handlers = set()
        for emb, handler in router._intents:
            handlers.add(handler)
        for h in handlers:
            f.write(f"Handler: {h.__doc__ or h.__name__}\n\n")

    print("Dumped successfully.")
except Exception as e:
    print(f"Error: {e}")
