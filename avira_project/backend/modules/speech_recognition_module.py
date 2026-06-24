"""
Module 1: Speech Recognition
Captures voice commands through microphone and converts to text.
Supports real microphone input (via SpeechRecognition) or simulated text input.
"""

import logging
import threading
import queue
import time

logger = logging.getLogger(__name__)


class SpeechRecognitionModule:
    """
    Handles voice-to-text conversion.
    Falls back to text input if microphone/SpeechRecognition is unavailable.
    """

    def __init__(self, language="en-US", timeout=5, phrase_time_limit=10):
        self.language = language
        self.timeout = timeout
        self.phrase_time_limit = phrase_time_limit
        self.is_listening = False
        self.command_queue = queue.Queue()
        self._recognizer = None
        self._microphone = None
        self._sr_available = False
        self._listen_thread = None

        self._init_recognizer()

    def _init_recognizer(self):
        """Initialize SpeechRecognition if available."""
        try:
            import speech_recognition as sr
            self._recognizer = sr.Recognizer()
            self._microphone = sr.Microphone()
            self._recognizer.energy_threshold = 300
            self._recognizer.dynamic_energy_threshold = True
            self._recognizer.pause_threshold = 0.8
            self._sr_available = True
            logger.info("SpeechRecognition initialized successfully.")
        except ImportError:
            logger.warning("SpeechRecognition not installed. Using text input fallback.")
            self._sr_available = False
        except Exception as e:
            logger.warning(f"Microphone init failed: {e}. Using text input fallback.")
            self._sr_available = False

    def listen_once(self) -> str | None:
        """
        Listen for a single voice command.
        Returns recognized text or None on failure.
        """
        if not self._sr_available:
            return self._text_input_fallback()

        try:
            import speech_recognition as sr
            with self._microphone as source:
                logger.info("Adjusting for ambient noise...")
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                logger.info("Listening for command...")
                audio = self._recognizer.listen(
                    source,
                    timeout=self.timeout,
                    phrase_time_limit=self.phrase_time_limit
                )

            # Using Vosk for absolute offline speech recognition
            # NOTE: This requires the Vosk model folder to be present in the backend root
            try:
                import json
                vosk_result_str = self._recognizer.recognize_vosk(audio)
                vosk_result = json.loads(vosk_result_str)
                text = vosk_result.get("text", "")
                
                if not text:
                    return None
                    
                logger.info(f"Recognized (Vosk): '{text}'")
                return text.lower().strip()
                
            except Exception as e:
                logger.error(f"Vosk error (did you forget the 'model' folder?): {e}")
                return self._text_input_fallback()

        except sr.WaitTimeoutError:
            logger.debug("Listening timed out. No speech detected.")
            return None
        except sr.UnknownValueError:
            logger.debug("Could not understand audio.")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in listen_once: {e}")
            return None

    def start_continuous_listening(self, callback):
        """
        Start a background thread that continuously listens and
        calls callback(text) for each recognized command.
        """
        if self.is_listening:
            logger.warning("Already listening.")
            return

        self.is_listening = True
        self._listen_thread = threading.Thread(
            target=self._continuous_listen_loop,
            args=(callback,),
            daemon=True
        )
        self._listen_thread.start()
        logger.info("Continuous listening started.")

    def stop_continuous_listening(self):
        """Stop the continuous listening thread."""
        self.is_listening = False
        logger.info("Continuous listening stopped.")

    def _continuous_listen_loop(self, callback):
        """Internal loop for continuous listening."""
        while self.is_listening:
            text = self.listen_once()
            if text:
                callback(text)
            time.sleep(0.1)

    def _text_input_fallback(self) -> str | None:
        """
        Fallback: read command from console input.
        Used when microphone is unavailable.
        """
        try:
            text = input(">>> Type your command: ").strip().lower()
            return text if text else None
        except (EOFError, KeyboardInterrupt):
            return None

    def get_status(self) -> dict:
        return {
            "sr_available": self._sr_available,
            "is_listening": self.is_listening,
            "language": self.language,
        }
