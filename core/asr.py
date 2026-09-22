import logging
import threading
import time

import numpy as np
import sounddevice as sd
import speech_recognition as sr

from core.config import (
    BLOCK_MS,
    CLAP_THRESHOLD,
    IDLE_TIMEOUT_S,
    Zia_WAKE_PHRASE,
    MIC_GAIN_FACTOR,
    POST_WAKE_COOLDOWN_S,
    SAMPLE_RATE,
    TRIGGER_COOLDOWN_S,
    tts_active,
    interrupt_event,
    INTERRUPT_PHRASES
)
from core.state import AssistantState, st
from core.tts import say_text

log = logging.getLogger(__name__)


class ASRPipeline:
    def __init__(self, wake_fn, strip_fn, dispatch_fn, sleep_fn):
        self._wake_word_hit = wake_fn
        self._strip_wake_prefix = strip_fn
        self._dispatch = dispatch_fn
        self._go_sleep = sleep_fn
        self.user_is_speaking = False

    def is_user_speaking(self) -> bool:
        return self.user_is_speaking

    def _check_barge_in(self, audio_data_bytes: bytes):
        if not tts_active.is_set():
            return
        audio_obj = sr.AudioData(audio_data_bytes, SAMPLE_RATE, 2)
        try:
            recognizer = sr.Recognizer()
            text = recognizer.recognize_google(audio_obj).lower().strip()
            if any(phrase in text for phrase in INTERRUPT_PHRASES):
                log.info("Barge-in phrase detected! Interrupting TTS...")
                interrupt_event.set()
                if "sleep" in text:
                    self._go_sleep()
                self.user_is_speaking = False
        except Exception:
            pass

    def listen_loop(self, input_idx: int):
        log.info("Initializing Google Speech Recognition...")
        recognizer = sr.Recognizer()

        speech_buffer = []
        self.user_is_speaking = False
        silence_frames = 0
        ENERGY_THRESHOLD = 300  # Lowered from 500 to increase sensitivity

        last_heard_text = ""
        last_voice_time = time.monotonic()
        last_silence_warn = time.monotonic()
        last_triggered = 0.0

        blocksize = int(SAMPLE_RATE * BLOCK_MS / 1000)

        log.info("============================================================")
        log.info("  Zia is listening via Google API...")
        log.info("============================================================")

        try:
            with sd.RawInputStream(
                device=input_idx,
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="int16",
                blocksize=blocksize,
            ) as stream:
                while True:
                    try:
                        raw_data, _overflowed = stream.read(blocksize)
                    except sd.PortAudioError as e:
                        log.warning("Audio read error: %s", e)
                        continue

                    if MIC_GAIN_FACTOR != 1.0:
                        samples = np.frombuffer(
                            bytes(raw_data), dtype=np.int16).copy()
                        samples = np.clip(
                            samples.astype(np.float32) * float(MIC_GAIN_FACTOR),
                            -32768, 32767
                        ).astype(np.int16)
                        audio_bytes = samples.tobytes()
                    else:
                        audio_bytes = bytes(raw_data)

                    # VAD + Google API Logic
                    samples = np.frombuffer(audio_bytes, dtype=np.int16)
                    rms = np.sqrt(np.mean(samples.astype(np.float32)**2))
                    is_speech_frame = rms > ENERGY_THRESHOLD

                    text = ""
                    tag = ""

                    if is_speech_frame:
                        if not self.user_is_speaking:
                            self.user_is_speaking = True
                        speech_buffer.append(audio_bytes)
                        silence_frames = 0

                        # Proactive barge-in chunking: if Zia is speaking, process buffer in chunks
                        if tts_active.is_set() and len(speech_buffer) > 45:
                            audio_data_bytes = b"".join(speech_buffer)
                            # Keep the last 15 frames for context to prevent cutting words in half
                            speech_buffer = speech_buffer[-15:]
                            threading.Thread(target=self._check_barge_in, args=(audio_data_bytes,), daemon=True).start()
                    else:
                        if self.user_is_speaking:
                            silence_frames += 1
                            speech_buffer.append(audio_bytes)

                            if silence_frames > 20:
                                self.user_is_speaking = False
                                audio_data_bytes = b"".join(speech_buffer)
                                speech_buffer = []
                                silence_frames = 0

                                if len(audio_data_bytes) > 16000:
                                    audio_obj = sr.AudioData(
                                        audio_data_bytes, SAMPLE_RATE, 2)
                                    try:
                                        text = recognizer.recognize_google(
                                            audio_obj).lower().strip()
                                        tag = "Final"
                                    except sr.UnknownValueError:
                                        pass
                                    except sr.RequestError as e:
                                        log.error("Google API error: %s", e)

                    if not text:
                        now = time.monotonic()
                        if (now - last_voice_time) > 90.0 and (now - last_silence_warn) > 90.0:
                            last_silence_warn = now
                            log.warning("No speech heard for 90s.")
                        continue

                    if text != last_heard_text:
                        last_heard_text = text
                        log.info("[%s] Heard: %r", tag, text)

                    if tts_active.is_set():
                        if text:
                            if any(phrase in text for phrase in INTERRUPT_PHRASES):
                                log.info("Barge-in phrase detected! Interrupting TTS...")
                                interrupt_event.set()
                                if "sleep" in text:
                                    self._go_sleep()
                                # Clear buffer so it doesn't process trailing noise
                                speech_buffer = []
                                self.user_is_speaking = False
                        continue

                    if text:
                        now = time.monotonic()
                        last_heard_text = text
                        last_voice_time = now

                    if st.state == AssistantState.ASLEEP:
                        if self._wake_word_hit(text):
                            if (now - last_triggered) < TRIGGER_COOLDOWN_S:
                                continue
                            last_triggered = now
                            log.info(
                                "Wake word detected: %r — entering AWAKE state.", text)
                            st.state = AssistantState.AWAKE
                            st.last_activity = now
                            st.post_wake_until = now + POST_WAKE_COOLDOWN_S
                            threading.Thread(target=say_text, args=(
                                Zia_WAKE_PHRASE,), daemon=True).start()

                            if tag == "Final":
                                remainder = self._strip_wake_prefix(text)
                                if remainder:
                                    log.info(
                                        "Inline command after wake: %r", remainder)
                                    threading.Thread(target=self._dispatch, args=(remainder,), daemon=True).start()

                    elif st.state == AssistantState.AWAKE:
                        if now < st.post_wake_until:
                            continue
                        if (now - st.last_activity) > IDLE_TIMEOUT_S:
                            log.info(
                                "Idle timeout (%.0fs) — entering ASLEEP state.", IDLE_TIMEOUT_S)
                            self._go_sleep()
                            continue
                        if tag == "Final" and text:
                            threading.Thread(target=self._dispatch, args=(text,), daemon=True).start()

        except KeyboardInterrupt:
            log.info("Interrupted.")
        except Exception as e:  # noqa: BLE001
            log.error("ASR loop error: %s", e)
