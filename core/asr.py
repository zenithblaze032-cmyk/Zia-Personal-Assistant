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
    JARVIS_WAKE_PHRASE,
    MIC_GAIN_FACTOR,
    POST_WAKE_COOLDOWN_S,
    SAMPLE_RATE,
    TRIGGER_COOLDOWN_S,
    mute_mic,
)
from core.state import AssistantState, st
from core.tts import say_text

log = logging.getLogger(__name__)

# Wake word functions (will be passed from main)
_wake_word_hit = None
_strip_wake_prefix = None
_dispatch = None
_go_sleep = None

def init_asr(wake_fn, strip_fn, dispatch_fn, sleep_fn):
    global _wake_word_hit, _strip_wake_prefix, _dispatch, _go_sleep
    _wake_word_hit = wake_fn
    _strip_wake_prefix = strip_fn
    _dispatch = dispatch_fn
    _go_sleep = sleep_fn

def listen_loop(input_idx: int):
    log.info("Initializing Google Speech Recognition...")
    recognizer = sr.Recognizer()
    
    speech_buffer = []
    is_speaking = False
    silence_frames = 0
    ENERGY_THRESHOLD = 500
    
    last_heard_text = ""
    last_voice_time = time.monotonic()
    last_silence_warn = time.monotonic()
    last_triggered = 0.0
    
    blocksize = int(SAMPLE_RATE * BLOCK_MS / 1000)
    
    log.info("============================================================")
    log.info("  JARVIS is listening via Google API...")
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
                    samples = np.frombuffer(bytes(raw_data), dtype=np.int16).copy()
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
                    if not is_speaking:
                        is_speaking = True
                    speech_buffer.append(audio_bytes)
                    silence_frames = 0
                else:
                    if is_speaking:
                        silence_frames += 1
                        speech_buffer.append(audio_bytes)
                        
                        if silence_frames > 20:
                            is_speaking = False
                            audio_data_bytes = b"".join(speech_buffer)
                            speech_buffer = []
                            silence_frames = 0
                            
                            if len(audio_data_bytes) > 16000:
                                audio_obj = sr.AudioData(audio_data_bytes, SAMPLE_RATE, 2)
                                try:
                                    text = recognizer.recognize_google(audio_obj).lower().strip()
                                    tag = "Final"
                                except sr.UnknownValueError:
                                    pass
                                except sr.RequestError as e:
                                    log.error("Google API error: %s", e)
                
                if not text:
                    now = time.monotonic()
                    if (now - last_voice_time) > 20.0 and (now - last_silence_warn) > 20.0:
                        last_silence_warn = now
                        log.warning("No speech heard for 20s.")
                    continue

                if text != last_heard_text:
                    last_heard_text = text
                    log.info("[%s] Heard: %r", tag, text)

                if mute_mic.is_set():
                    speech_buffer = []
                    is_speaking = False
                    continue
                
                if text:
                    now = time.monotonic()
                    last_heard_text = text
                    last_voice_time = now
                    
                if st.state == AssistantState.ASLEEP:
                    if _wake_word_hit(text):
                        if (now - last_triggered) < TRIGGER_COOLDOWN_S:
                            continue
                        last_triggered = now
                        log.info("Wake word detected: %r — entering AWAKE state.", text)
                        st.state = AssistantState.AWAKE
                        st.last_activity = now
                        st.post_wake_until = now + POST_WAKE_COOLDOWN_S
                        threading.Thread(target=say_text, args=(JARVIS_WAKE_PHRASE,), daemon=True).start()
                        
                        if tag == "Final":
                            remainder = _strip_wake_prefix(text)
                            if remainder:
                                log.info("Inline command after wake: %r", remainder)
                                _dispatch(remainder)

                elif st.state == AssistantState.AWAKE:
                    if now < st.post_wake_until:
                        continue
                    if (now - st.last_activity) > IDLE_TIMEOUT_S:
                        log.info("Idle timeout (%.0fs) — entering ASLEEP state.", IDLE_TIMEOUT_S)
                        _go_sleep()
                        continue
                    if tag == "Final" and text:
                        _dispatch(text)
                        
    except KeyboardInterrupt:
        log.info("Interrupted.")
    except Exception as e:  # noqa: BLE001
        log.error("ASR loop error: %s", e)
