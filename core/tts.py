import asyncio
import logging
import threading

import edge_tts
import miniaudio

from core.config import Zia_TTS_VOICE, tts_active, interrupt_event

log = logging.getLogger(__name__)

_Zia_tts = None
_Zia_tts_lock = threading.Lock()
_tts_playback_lock = threading.Lock()
USE_PIPER_TTS = True


def _get_piper_tts():
    """Return the ZiaTTS singleton, loading it on first call."""
    global _Zia_tts
    if _Zia_tts is not None:
        return _Zia_tts
    with _Zia_tts_lock:
        if _Zia_tts is not None:
            return _Zia_tts
        try:
            from core.piper_tts import ZiaTTS
            _Zia_tts = ZiaTTS(auto_download=True)
            return _Zia_tts
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "Piper TTS unavailable (%s); will fall back to Edge TTS.", exc)
            return None


def say_text(text: str) -> None:
    """Main TTS function."""
    if not text:
        return

    with _tts_playback_lock:
        interrupt_event.clear()
        tts_active.set()
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
            tts_active.clear()


async def _say_via_edge_tts_async(text: str) -> None:
    """Fallback: synthesize with free Microsoft Edge neural TTS."""
    import os
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        temp_path = fp.name
    try:
        import os
        rate = os.environ.get("Zia_TTS_RATE", "+5%")
        pitch = os.environ.get("Zia_TTS_PITCH", "-10Hz")
        c = edge_tts.Communicate(text, Zia_TTS_VOICE, rate=rate, pitch=pitch)
        await c.save(temp_path)

        device = miniaudio.PlaybackDevice()
        stream = miniaudio.stream_file(temp_path)
        device.start(stream)

        import time  # noqa: F401
        while device.running:
            if interrupt_event.is_set():
                device.stop()
                log.info("Edge TTS playback interrupted by user.")
                break
            await asyncio.sleep(0.05)
    except Exception as exc:  # noqa: BLE001
        log.warning("[Edge TTS] Failed: %s", exc)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
