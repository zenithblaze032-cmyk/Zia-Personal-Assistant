import logging
import requests

log = logging.getLogger(__name__)

def take_weather(match, ctx):
    try:
        # Get location via IP
        loc_resp = requests.get("http://ip-api.com/json", timeout=5).json()
        lat = loc_resp.get("lat", 40.71)
        lon = loc_resp.get("lon", -74.00)
        city = loc_resp.get("city", "New York")
        
        # Get weather
        weather_resp = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true",
            timeout=5
        ).json()
        
        temp = weather_resp["current_weather"]["temperature"]
        ctx.say(f"The current temperature in {city} is {temp} degrees.")
    except Exception as e:
        log.error(f"Weather error: {e}")
        ctx.say("I couldn't fetch the weather right now, sir.")

def register(router):
    router.register(r"(?i)\b(?:what is the weather|weather today|how is the weather|what's the weather)\b", take_weather)
    router.register_intent([
        "what is the weather like right now",
        "tell me the current weather",
        "is it going to rain today",
        "do I need an umbrella today",
        "how hot is it outside"
    ], take_weather)
