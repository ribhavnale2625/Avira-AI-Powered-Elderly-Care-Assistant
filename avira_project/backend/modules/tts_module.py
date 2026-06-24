"""
Module 2: Text-to-Speech (TTS)
Converts assistant responses to spoken audio.
Supports pyttsx3 (offline) or gTTS (online) with console fallback.
"""

import logging
import threading
import os
import tempfile

logger = logging.getLogger(__name__)


class TextToSpeechModule:
    """
    Handles converting text responses to spoken audio.
    Priority: pyttsx3 (offline) → gTTS (online) → print fallback
    """

    def __init__(self, rate=150, volume=0.9, voice_gender="female"):
        self.rate = rate
        self.volume = volume
        self.voice_gender = voice_gender
        self._engine = None
        self._tts_mode = "none"
        self._lock = threading.Lock()

        self._init_engine()

    def _init_engine(self):
        """Initialize TTS engine with fallback chain."""
        # Try ElevenLabs first (Best quality, requires internet)
        self.elevenlabs_api_key = os.environ.get("ELEVENLABS_API_KEY", "ffde3966c89b2105c9f3cadbfa0367dcf0665b07d1f60600c5568f2fad082cd4")
        self.elevenlabs_voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "GCnQQItgI1yFf0tUBLZv")  # Required female voice

        if self.elevenlabs_api_key:
            try:
                import requests
                import pygame
                pygame.mixer.init()
                self._tts_mode = "elevenlabs"
                logger.info("TTS initialized with ElevenLabs (online mode).")
                return
            except ImportError:
                logger.info("requests or pygame not available for ElevenLabs. Falling back.")
            except Exception as e:
                logger.warning(f"ElevenLabs init failed: {e}")

        # Try pyttsx3 first (offline, best for elderly users - no internet needed)
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty('rate', self.rate)
            self._engine.setProperty('volume', self.volume)

            # Select voice by gender
            voices = self._engine.getProperty('voices')
            if voices:
                for voice in voices:
                    if self.voice_gender.lower() in voice.name.lower():
                        self._engine.setProperty('voice', voice.id)
                        break

            self._tts_mode = "pyttsx3"
            logger.info("TTS initialized with pyttsx3 (offline mode).")
            return
        except ImportError:
            logger.info("pyttsx3 not available.")
        except Exception as e:
            logger.warning(f"pyttsx3 init failed: {e}")

        # Try gTTS (requires internet)
        try:
            from gtts import gTTS
            import pygame
            pygame.mixer.init()
            self._tts_mode = "gtts"
            logger.info("TTS initialized with gTTS + pygame.")
            return
        except ImportError:
            logger.info("gTTS/pygame not available.")
        except Exception as e:
            logger.warning(f"gTTS init failed: {e}")

        # Fallback: print to console
        self._tts_mode = "console"
        logger.warning("TTS falling back to console print mode.")

    def speak(self, text: str, blocking: bool = True):
        """
        Speak the given text aloud.
        
        Args:
            text: The text to speak.
            blocking: If True, wait until speech completes.
        """
        if not text or not text.strip():
            return

        logger.info(f"TTS [{self._tts_mode}]: {text}")

        if blocking:
            self._speak_text(text)
        else:
            thread = threading.Thread(target=self._speak_text, args=(text,), daemon=True)
            thread.start()

    def _speak_text(self, text: str):
        """Internal method to perform TTS (DISABLED - Frontend handles voice)."""
        # All sound output is disabled here to prevent duplicate voices.
        # We only print to console/logs.
        self._speak_console(text)

    def _speak_elevenlabs(self, text: str):
        try:
            import requests
            import pygame

            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.elevenlabs_voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.elevenlabs_api_key
            }
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                },
                "language_code": "mr" if any(c in text for c in "\u0900-\u097F") else "en"
            }

            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(response.content)
                tmp_path = f.name

            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                import time
                time.sleep(0.1)

            try:
                pygame.mixer.music.unload()
            except AttributeError:
                pass  # only available in pygame >= 2.0.0
                
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"ElevenLabs speak error: {e}")
            self._speak_console(text)

    def _speak_pyttsx3(self, text: str):
        try:
            self._engine.say(text)
            self._engine.runAndWait()
        except Exception as e:
            logger.error(f"pyttsx3 speak error: {e}")
            self._speak_console(text)

    def _speak_gtts(self, text: str):
        try:
            from gtts import gTTS
            import pygame

            # Detect language for gTTS
            lang_code = 'hi' if any(c in text for c in "\u0900-\u097F") else 'en'
            # Check for Marathi specific characters if needed, but gTTS 'hi' works well for both
            if any(c in text for c in ["\u0933", "\u091e"]): lang_code = 'hi' 
            
            tts = gTTS(text=text, lang=lang_code, slow=False)
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tmp_path = f.name
            tts.save(tmp_path)

            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                import time
                time.sleep(0.1)

            os.unlink(tmp_path)
        except Exception as e:
            logger.error(f"gTTS speak error: {e}")
            self._speak_console(text)

    def _speak_console(self, text: str):
        """Fallback: print response to console."""
        print(f"\n[ASSISTANT SPEAKS]: {text}\n")

    def set_rate(self, rate: int):
        """Change speech rate (words per minute)."""
        self.rate = rate
        if self._tts_mode == "pyttsx3" and self._engine:
            self._engine.setProperty('rate', rate)

    def set_volume(self, volume: float):
        """Change speech volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        if self._tts_mode == "pyttsx3" and self._engine:
            self._engine.setProperty('volume', self.volume)

    def get_status(self) -> dict:
        return {
            "tts_mode": self._tts_mode,
            "rate": self.rate,
            "volume": self.volume,
            "voice_gender": self.voice_gender,
        }
