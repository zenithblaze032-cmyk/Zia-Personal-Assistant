# How to Change Jarvis's Voice (Piper TTS)

Jarvis now uses a **config-driven** Piper TTS system. You can switch between male and
female voices just by editing **one line in your `.env` file** — no code changes needed.
New voices are **downloaded automatically** on first use (~60 MB each, one time only).

## Quick Start (30 seconds)

1. Open the `.env` file in the project root.
2. Add (or uncomment) this line with the voice you want:

   ```env
   JARVIS_PIPER_VOICE=en_US-ryan-high
   ```

3. Restart Jarvis (`run.bat`). The new voice downloads automatically and starts speaking.

## Recommended Voices (curated Top 5 male & female)

| # | Male voices | Character | | # | Female voices | Character |
|---|---|---|---|---|---|---|
| 1 | `en_GB-alan-medium` ★ default | Deep British butler — classic JARVIS | 1 | `en_GB-jenny_dioco-medium` | Refined RP British — "Pepper Potts" |
| 2 | `en_US-ryan-high` | Warm, confident American — movie-trailer tone | 2 | `en_GB-southern_english_female-low` | Posh Southern English |
| 3 | `en_GB-northern_english_male-medium` | Rough Northern English — Batman-esque | 3 | `en_US-amy-medium` | Soft, friendly — Siri-like |
| 4 | `en_US-joe-medium` | Gravelly, laid-back American | 4 | `en_US-lessac-high` | Clear, professional narrator |
| 5 | `en_US-danny-low` | Deep, energetic young male | 5 | `en_US-kathleen-low` | Calm, warm, low-key |

> Tip: `en_US-amy-medium` is already downloaded locally, so you can test a female
> voice instantly with zero download.

## See the Full Voice Catalog

Run the built-in voice lister:

```bash
python core/piper_tts.py --list
```

Output:

```
Male voices:
  • en_GB-alan-medium  ← current default
  • en_US-ryan-high
  • en_GB-northern_english_male-medium
  • en_US-joe-medium
  • en_US-danny-low

Female voices:
  • en_GB-jenny_dioco-medium
  • en_GB-southern_english_female-low
  • en_US-amy-medium
  • en_US-lessac-high
  • en_US-kathleen-low
```

## Try a Voice Before Switching (standalone test)

Preview any voice without restarting the full assistant:

```bash
# Speak with the voice currently set in .env
python core/piper_tts.py "All systems online, sir."

# Force a specific voice for one test run
venv\Scripts\python.exe -c "from core.piper_tts import JarvisTTS; JarvisTTS('en_US-ryan-high').speak('Testing one two three.')"
```

## Using Any Other Piper Voice (not in the catalog)

Jarvis isn't limited to the 10 curated voices — **any** voice from the official Piper
catalog works. Browse audio samples at [rhasspy.github.io/piper-samples](https://rhasspy.github.io/piper-samples/),
note the exact voice name (e.g. `en_GB-alba-medium`), and set it:

```env
JARVIS_PIPER_VOICE=en_GB-alba-medium
```

The name must follow Piper's convention `<locale>-<speaker>-<quality>`:
- `<locale>` — language/region, e.g. `en_GB`, `en_US`
- `<speaker>` — the voice's name, e.g. `alba`
- `<quality>` — one of `low`, `medium`, `high` (higher = better quality, bigger file)

An invalid name is rejected at startup with a clear error message, so typos are easy to spot.

## Managing Downloaded Models

All voice models live in `models/voice/`. Each voice = one `.onnx` file + one `.onnx.json` config:

```
models/voice/
├── en_GB-alan-medium.onnx        (~63 MB)
├── en_GB-alan-medium.onnx.json
├── en_US-amy-medium.onnx
└── ...
```

To free up disk space, just delete the `.onnx` file of a voice you no longer use —
it will be re-downloaded automatically if you switch back to it later.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `HTTP Error 404` on download | Voice name is misspelled — check the name against the samples page. |
| `Invalid Piper voice name` | Name must match `<locale>-<speaker>-<quality>`, e.g. `en_US-ryan-high`. |
| Still hearing the old voice | Restart Jarvis — the voice is loaded once at startup. |

---

### (Optional) Voice Speed
You can also tune pacing in `.env`:
```env
JARVIS_PIPER_LENGTH_SCALE=1.15
```
- `1.0` = Default speed
- `0.85` = Faster
- `1.15` = Slower (more natural pacing)

> Note: the bundled `piper-tts` 1.8 Python API does not yet expose `length_scale`
> in `synthesize()`, so this setting is currently reserved for when that support lands.

