# How to Change Jarvis's Voice (Piper TTS)

Piper TTS has hundreds of free, offline voice models. If you ever want to change Jarvis's voice again, follow these simple steps!

## Step 1: Find a Voice You Like
1. Go to the official Piper voice preview page: [rhasspy.github.io/piper-samples](https://rhasspy.github.io/piper-samples/)
2. Listen to the audio samples and pick a voice you like. 
3. Note the exact **name** and **quality** of the voice. (e.g., `en_GB-alba-medium` or `en_US-kusal-medium`).

## Step 2: Update the Code
1. Open the file `core/piper_tts.py` in your code editor.
2. Scroll to **Line 33**, where the model paths are defined.
3. Replace the `alan-medium` file names with your new voice's name.

For example, if you chose `en_GB-alba-medium`, change the code to look like this:

```python
MODEL_ONNX = MODELS_DIR / "en_GB-alba-medium.onnx"
MODEL_JSON  = MODELS_DIR / "en_GB-alba-medium.onnx.json"

MODEL_ONNX_URL = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main"
    "/en/en_GB/alba/medium/en_GB-alba-medium.onnx"
)
MODEL_JSON_URL = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main"
    "/en/en_GB/alba/medium/en_GB-alba-medium.onnx.json"
)
```
*(Notice how the URL path uses `.../en_GB/alba/medium/...` based on the voice name).*

## Step 3: Restart Jarvis
Save the file, close any running Jarvis terminal, and run `run.bat` again. 

Jarvis will automatically see that the new model files are missing, download them directly into the `models/voice` folder, and load up your new voice instantly!

---
### (Optional) Tuning the Voice Speed
If the new voice speaks too fast or too slow, you can tweak the speed in your `.env` file:
```env
JARVIS_PIPER_LENGTH_SCALE=1.15
```
- `1.0` = Default speed
- `0.85` = Faster
- `1.15` = Slower (More natural pacing)
