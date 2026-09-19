"""
core/piper_tts.py — Zia Local Offline TTS Module
=============================================
Uses Piper TTS with offline voice models from the
rhasspy/piper-voices catalog on HuggingFace:
https://huggingface.co/rhasspy/piper-voices

Usage:
    from core.piper_tts import ZiaTTS
    tts = ZiaTTS()
    tts.speak("All systems online, sir.")

Standalone test:
    python core/piper_tts.py
"""

from __future__ import annotations

import logging
import os
import re
import sys
import urllib.request
from pathlib import Path

import numpy as np
import sounddevice as sd

log = logging.getLogger("Zia.tts")

# ---------------------------------------------------------------------------
# Voice catalog & model paths
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent.parent          # project root
MODELS_DIR = _HERE / "models" / "voice"

# Default voice (Zia-style British male)
DEFAULT_PIPER_VOICE = "en_GB-alan-medium"

# Curated top-5 male & female Piper voices.
# All are downloadable offline models from rhasspy/piper-voices (HuggingFace).
#
# MALE
# ── en_GB-alan-medium          — deep, formal British butler (classic Zia feel) ★ default
# ── en_US-ryan-high            — warm, confident American male (movie-trailer tone)
# ── en_GB-northern_english_male-medium — rough Northern English male (Batman-esque)
# ── en_US-joe-medium           — gravelly, laid-back American male
# ── en_US-danny-low            — deep, low-pitched young male (energetic)
#
# FEMALE
# ── en_GB-jenny_dioco-medium   — refined RP British female (Pepper Potts vibe)
# ── en_GB-southern_english_female-low — posh Southern English female
# ── en_US-amy-medium           — soft, friendly American female (Siri-like)
# ── en_US-lessac-high          — clear, professional American female narrator
# ── en_US-kathleen-low         — calm, warm low-key American female
#
MALE_VOICES = (
    "en_GB-alan-medium",
    "en_US-ryan-high",
    "en_GB-northern_english_male-medium",
    "en_US-joe-medium",
    "en_US-danny-low",
)
FEMALE_VOICES = (
    "en_GB-jenny_dioco-medium",
    "en_GB-southern_english_female-low",
    "en_US-amy-medium",
    "en_US-lessac-high",
    "en_US-kathleen-low",
)


def _voice_paths(voice_name: str) -> tuple[Path, Path]:
    """Return (onnx_path, json_path) for a Piper voice name like 'en_GB-alan-medium'."""
    return MODELS_DIR / f"{voice_name}.onnx", MODELS_DIR / f"{voice_name}.onnx.json"


def _voice_urls(voice_name: str) -> tuple[str, str]:
    """Build HuggingFace download URLs for a Piper voice name.

    Voice names follow the Piper convention '<locale>-<speaker>-<quality>',
    e.g. 'en_GB-alan-medium' → locale=en_GB, speaker=alan, quality=medium.
    """
    m = re.match(
        r"^(?P<locale>[a-z]{2}_[A-Z]{2})-(?P<speaker>.+)-(?P<quality>low|medium|high)$", voice_name)
    if not m:
        raise ValueError(
            f"Invalid Piper voice name: {voice_name!r}. "
            "Expected format '<locale>-<speaker>-<quality>', e.g. 'en_GB-alan-medium'."
        )
    base = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
    lang = m.group("locale").split("_")[0]
    path = f"/{lang}/{m.group('locale')}/{m.group('speaker')}/{m.group('quality')}/{voice_name}"
    return f"{base}{path}.onnx", f"{base}{path}.onnx.json"


def list_voices() -> None:
    """Print the curated male/female voice catalog."""
    print("\n  Male voices:")
    for v in MALE_VOICES:
        marker = "  ← current default" if v == DEFAULT_PIPER_VOICE else ""
        print(f"    • {v}{marker}")
    print("\n  Female voices:")
    for v in FEMALE_VOICES:
        print(f"    • {v}")
    print(
        "\n  To switch voices, set Zia_PIPER_VOICE in .env, e.g.:\n"
        "      Zia_PIPER_VOICE=en_US-ryan-high\n"
        "  (any Piper voice from rhasspy/piper-voices works — it will be\n"
        "   downloaded automatically on first use.)\n"
    )


# ---------------------------------------------------------------------------
# One-time model download
# ---------------------------------------------------------------------------

def _download_file(url: str, dest: Path, label: str) -> None:
    """Download a file with a progress indicator."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    log.info("Downloading %s …", label)

    def _progress(block: int, block_sz: int, total: int) -> None:
        if total > 0:
            pct = min(100, block * block_sz * 100 // total)
            mb_done = block * block_sz / 1_048_576
            mb_total = total / 1_048_576
            print(
                f"\r  {label}: {pct:3d}%  ({mb_done:.1f} / {mb_total:.1f} MB)",
                end="",
                flush=True,
            )

    try:
        urllib.request.urlretrieve(url, tmp, _progress)
        print()  # newline after progress bar
        tmp.replace(dest)
        log.info("Saved → %s", dest)
    except Exception as exc:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Failed to download {label}: {exc}") from exc


def _resolve_voice_name() -> str:
    """Pick the active voice: Zia_PIPER_VOICE env → default."""
    return (os.environ.get("Zia_PIPER_VOICE") or DEFAULT_PIPER_VOICE).strip()


def ensure_model_files(voice_name: str = DEFAULT_PIPER_VOICE) -> None:
    """Download ONNX model and JSON config for `voice_name` if they are missing."""
    model_path, json_path = _voice_paths(voice_name)
    onnx_url, json_url = _voice_urls(voice_name)

    missing = []
    if not model_path.exists():
        missing.append((onnx_url, model_path, f"{voice_name}.onnx"))
    if not json_path.exists():
        missing.append((json_url, json_path, f"{voice_name}.onnx.json"))

    if not missing:
        return

    log.info(
        "Piper voice '%s' not found in %s. Downloading %d file(s) — one-time setup.",
        voice_name,
        MODELS_DIR,
        len(missing),
    )
    for url, dest, label in missing:
        _download_file(url, dest, label)
    log.info("Piper voice '%s' ready.", voice_name)


# ---------------------------------------------------------------------------
# ZiaTTS class
# ---------------------------------------------------------------------------

class ZiaTTS:
    """
    Offline, local TTS using Piper + the Zia voice model.

    The model is loaded once at instantiation; `speak()` is thread-safe
    (each call creates its own in-memory audio buffer).
    """

    def __init__(
        self,
        voice_name: str | None = None,
        *,
        auto_download: bool = True,
    ) -> None:
        voice_name = (voice_name or _resolve_voice_name()).strip()
        self.voice_name = voice_name
        model_path, config_path = _voice_paths(voice_name)

        if auto_download:
            ensure_model_files(voice_name)

        if not model_path.exists():
            raise FileNotFoundError(
                f"Piper model not found: {model_path}\n"
                "Run ensure_model_files() or set auto_download=True."
            )

        log.info("Loading Piper voice '%s' from %s …", voice_name, model_path)
        try:
            from piper import PiperVoice  # type: ignore[import]
            self._voice = PiperVoice.load(
                str(model_path),
                config_path=str(config_path),
            )
        except ImportError as exc:
            raise ImportError(
                "piper-tts is not installed. Run: pip install piper-tts"
            ) from exc
        log.info("Piper TTS ready (voice: %s).", voice_name)

    # ------------------------------------------------------------------

    def speak(self, text: str) -> None:
        """
        Synthesize `text` to an in-memory WAV buffer and play it immediately.

        The call blocks until playback finishes. Logs and swallows any errors
        so the main program is never disrupted by a TTS failure.
        """
        text = text.strip()
        if not text:
            return
        try:
            self._synthesize_and_play(text)
        except Exception as exc:  # noqa: BLE001
            log.warning("TTS speak() error: %s", exc)

    def _synthesize_and_play(self, text: str) -> None:
        """Internal: synthesize via piper-tts 1.8+ API → sounddevice playback.

        piper-tts >= 1.8 returns Iterable[AudioChunk] from synthesize().
        Each chunk exposes:
          .audio_int16_bytes  — raw PCM int16 bytes
          .sample_rate        — e.g. 22050
          .sample_channels    — 1 (mono) or 2 (stereo)
        """
        # Collect all audio chunks.
        # Collect all audio chunks.
        all_pcm: list[bytes] = []
        sample_rate: int = 22050
        n_channels: int = 1

        # The Python piper-tts module currently does not support length_scale in synthesize()
        for chunk in self._voice.synthesize(text):
            all_pcm.append(chunk.audio_int16_bytes)
            sample_rate = chunk.sample_rate
            n_channels = chunk.sample_channels

        if not all_pcm:
            raise RuntimeError("Piper synthesize() returned no audio chunks.")

        raw_bytes = b"".join(all_pcm)

        # Convert raw int16 PCM → float32 in [-1, 1] for sounddevice.
        pcm_i16 = np.frombuffer(raw_bytes, dtype=np.int16)

        # If stereo, reshape to (frames, channels) as sounddevice expects.
        if n_channels > 1:
            pcm_i16 = pcm_i16.reshape(-1, n_channels)

        pcm_f32 = pcm_i16.astype(np.float32) / 32768.0

        # Pad with a small amount of silence at the start and end.
        # Piper TTS commonly truncates the first and last words of an
        # utterance because it emits no leading/trailing silence — so opening
        # lines (e.g. the wake phrase) and closing lines (e.g. the exit phrase)
        # lose their final words.  200 ms of silence on each side ensures the
        # full speech is audible and the last word isn't clipped mid-playback.
        silence_frames = int(sample_rate * 0.2)
        if pcm_f32.ndim == 2:
            pad = np.zeros(
                (silence_frames, pcm_f32.shape[1]), dtype=pcm_f32.dtype)
        else:
            pad = np.zeros(silence_frames, dtype=pcm_f32.dtype)
        pcm_f32 = np.concatenate([pad, pcm_f32, pad])

        sd.play(pcm_f32, samplerate=sample_rate)
        sd.wait()

    # ------------------------------------------------------------------

    def speak_async(self, text: str) -> None:
        """
        Non-blocking variant — fire-and-forget in a daemon thread.
        Use this when you don't want TTS to block your main thread.
        """
        import threading
        threading.Thread(target=self.speak, args=(text,), daemon=True).start()


# ---------------------------------------------------------------------------
# Standalone test / CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    test_phrase = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "All systems online and operational, sir."
    )

    print()
    print("  Zia TTS — Standalone Test")
    print("  ─────────────────────────────────────────────")
    print(f"  Active voice: {_resolve_voice_name()}")
    print(f'  Phrase      : "{test_phrase}"')
    print()

    if "--list" in sys.argv or "-l" in sys.argv:
        list_voices()
    else:
        try:
            tts = ZiaTTS()
            print("  Speaking …")
            tts.speak(test_phrase)
            print("  Done.")
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR: {e}", file=sys.stderr)
            sys.exit(1)
