import asyncio
import logging
import threading

import edge_tts
import miniaudio

from core.config import JARVIS_TTS_VOICE, mute_mic

log = logging.getLogger(__name__)

_jarvis_tts = None
_jarvis_tts_lock = threading.Lock()
USE_PIPER_TTS = True

def _get_piper_tts():
    """Return the JarvisTTS singleton, loading it on first call."""
    global _jarvis_tts
    if _jarvis_tts is not None:
        return _jarvis_tts
    with _jarvis_tts_lock:
        if _jarvis_tts is not None:
            return _jarvis_tts
        try:
            from core.piper_tts import JarvisTTS
            _jarvis_tts = JarvisTTS(auto_download=True)
            return _jarvis_tts
        except Exception as exc:  # noqa: BLE001
            log.warning("Piper TTS unavailable (%s); will fall back to Edge TTS.", exc)
            return None

def say_text(text: str) -> None:
    """Main TTS function."""
    if not text:
        return
        
    mute_mic.set()
    try:
        if USE_PIPER_TTS:
            tts = _get_piper_tts()
            if tts is not None:
                log.info("[Piper TTS] Speaking: %r", text)
                tts.speak(text)
                return
        
        log.info("[Edge TTS] Speaking: %r", text)
        asyncio.run(_say_via_edge_tts_async(text))
    finally:
        mute_mic.clear()

async def _say_via_edge_tts_async(text: str) -> None:
    """Fallback: synthesize with free Microsoft Edge neural TTS."""
    import os
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        temp_path = fp.name
    try:
        c = edge_tts.Communicate(text, JARVIS_TTS_VOICE)
        await c.save(temp_path)
        
        device = miniaudio.PlaybackDevice()
        stream = miniaudio.stream_file(temp_path)
        device.start(stream)
        
        import time  # noqa: F401
        while device.running:
            await asyncio.sleep(0.05)
    except Exception as exc:  # noqa: BLE001
        log.warning("[Edge TTS] Failed: %s", exc)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
