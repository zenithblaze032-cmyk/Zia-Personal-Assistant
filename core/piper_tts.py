"""
core/piper_tts.py — JARVIS Local Offline TTS Module
=============================================
Uses Piper TTS with the open-source JARVIS voice model (en_GB/jarvis/high)
from HuggingFace: https://huggingface.co/jgkawell/jarvis

Usage:
    from core.piper_tts import JarvisTTS
    tts = JarvisTTS()
    tts.speak("All systems online, sir.")

Standalone test:
    python core/piper_tts.py
"""

from __future__ import annotations

import logging
import sys
import urllib.request
from pathlib import Path

import numpy as np
import sounddevice as sd

log = logging.getLogger("jarvis.tts")

# ---------------------------------------------------------------------------
# Model paths & download URLs
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent.parent          # project root
MODELS_DIR = _HERE / "models" / "voice"
MODEL_ONNX = MODELS_DIR / "jarvis-high.onnx"
MODEL_JSON  = MODELS_DIR / "jarvis-high.onnx.json"

MODEL_ONNX_URL = (
    "https://huggingface.co/jgkawell/jarvis/resolve/main"
    "/en/en_GB/jarvis/high/jarvis-high.onnx"
)
MODEL_JSON_URL = (
    "https://huggingface.co/jgkawell/jarvis/resolve/main"
    "/en/en_GB/jarvis/high/jarvis-high.onnx.json"
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


def ensure_model_files() -> None:
    """Download ONNX model and JSON config if they are missing."""
    missing = []
    if not MODEL_ONNX.exists():
        missing.append((MODEL_ONNX_URL, MODEL_ONNX, "jarvis-high.onnx (~85 MB)"))
    if not MODEL_JSON.exists():
        missing.append((MODEL_JSON_URL, MODEL_JSON, "jarvis-high.onnx.json"))

    if not missing:
        return

    log.info(
        "JARVIS voice model not found in %s. Downloading %d file(s) — one-time setup.",
        MODELS_DIR,
        len(missing),
    )
    for url, dest, label in missing:
        _download_file(url, dest, label)
    log.info("JARVIS voice model ready.")


# ---------------------------------------------------------------------------
# JarvisTTS class
# ---------------------------------------------------------------------------

class JarvisTTS:
    """
    Offline, local TTS using Piper + the JARVIS voice model.

    The model is loaded once at instantiation; `speak()` is thread-safe
    (each call creates its own in-memory audio buffer).
    """

    def __init__(
        self,
        model_path: str | Path = MODEL_ONNX,
        config_path: str | Path = MODEL_JSON,
        *,
        auto_download: bool = True,
    ) -> None:
        model_path = Path(model_path)
        config_path = Path(config_path)

        if auto_download:
            ensure_model_files()

        if not model_path.exists():
            raise FileNotFoundError(
                f"Piper model not found: {model_path}\n"
                "Run ensure_model_files() or set auto_download=True."
            )

        log.info("Loading JARVIS voice model from %s …", model_path)
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
        log.info("JARVIS TTS ready (Piper / en_GB jarvis-high).")

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
        all_pcm: list[bytes] = []
        sample_rate: int = 22050
        n_channels: int = 1

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
            pad = np.zeros((silence_frames, pcm_f32.shape[1]), dtype=pcm_f32.dtype)
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
    print("  JARVIS TTS — Standalone Test")
    print("  ─────────────────────────────────────────────")
    print(f"  Voice model : {MODEL_ONNX}")
    print(f'  Phrase      : "{test_phrase}"')
    print()

    try:
        tts = JarvisTTS()
        print("  Speaking …")
        tts.speak(test_phrase)
        print("  Done.")
    except Exception as e:  # noqa: BLE001
        print(f"  ERROR: {e}", file=sys.stderr)
        sys.exit(1)
