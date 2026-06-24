"""
Elderly Care Voice Assistant - Main Orchestrator
Coordinates all modules: speech, TTS, commands, emotion, alerts, smart home.
"""

import logging
import threading
import time
import datetime
import json
import os

# Module imports
from modules.speech_recognition_module import SpeechRecognitionModule
from modules.tts_module import TextToSpeechModule
from modules.command_processor import CommandProcessor
from modules.alert_module import EmergencyAlertModule
from modules.smart_home_module import SmartHomeModule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/assistant.log", mode="a", encoding="utf-8"),
    ]
)
logger = logging.getLogger("ElderCareAssistant")

os.makedirs("logs", exist_ok=True)


class ElderCareAssistant:
    """
    Main coordinator for the Elderly Care Voice Assistant.
    
    Manages the interaction loop:
    1. Listen for voice input
    2. Detect emotion from speech/text
    3. Process command
    4. Respond with TTS
    5. Handle smart home / SOS side effects
    """

    def __init__(self, config: dict = None):
        self.config = config or self._default_config()
        self.is_running = False
        self._sos_callback = None
        self._device_update_callback = None
        self._response_callback = None
        self._conversation_history = []

        # ── Caregiver features ──────────────────────────────────────
        self._caregiver_messages = []       # queue of messages from caregiver
        self._caregiver_sent_log = []       # log of delivered messages
        self._reminders = []                # active scheduled reminders
        self._reminder_history = []         # past fired reminders
        self._emotion_history = []          # timestamped emotion records
        self._reminder_thread = None
        self._last_active = datetime.datetime.now().isoformat()
        self._pending_frontend_events = []  # queue for React polling
        self._current_language = 'en'        # active language (en/hi/mr)

        # Multilingual greeting templates
        self._greetings = {
            'en': {
                'morning': 'Good morning',
                'afternoon': 'Good afternoon',
                'evening': 'Good evening',
                'body': "{greeting}, {name}! I'm your care assistant, always here for you. You can ask me to play music, check the time, control your home appliances, or just have a nice conversation. And if you ever need help urgently, just say 'Help me' or press the SOS button.",
            },
            'hi': {
                'morning': '\u0938\u0941\u092a\u094d\u0930\u092d\u093e\u0924',
                'afternoon': '\u0928\u092e\u0938\u094d\u0915\u093e\u0930',
                'evening': '\u0936\u0941\u092d \u0938\u0902\u0927\u094d\u092f\u093e',
                'body': "{greeting}, {name}! \u092e\u0948\u0902 \u0906\u092a\u0915\u0940 \u0935\u094d\u092f\u0915\u094d\u0924\u093f\u0917\u0924 \u0926\u0947\u0916\u092d\u093e\u0932 \u0938\u0939\u093e\u092f\u0915 AVIRA \u0939\u0942\u0901\u0964 \u0906\u092a \u092e\u0941\u091d\u0938\u0947 \u0938\u0902\u0917\u0940\u0924, \u0938\u092e\u092f, \u0918\u0930 \u0915\u0947 \u0909\u092a\u0915\u0930\u0923 \u092f\u093e \u092c\u093e\u0924\u091a\u0940\u0924 \u0915\u0947 \u092c\u093e\u0930\u0947 \u092e\u0947\u0902 \u092a\u0942\u091b \u0938\u0915\u0924\u0947 \u0939\u0948\u0902\u0964 \u0905\u0917\u0930 \u0906\u092a\u0915\u094b \u0915\u092d\u0940 \u0924\u0941\u0930\u0902\u0924 \u092e\u0926\u0926 \u091a\u093e\u0939\u093f\u090f, \u0924\u094b '\u092e\u0926\u0926 \u0915\u0930\u094b' \u092c\u094b\u0932\u0947\u0902 \u092f\u093e SOS \u092c\u091f\u0928 \u0926\u092c\u093e\u090f\u0902\u0964",
            },
            'mr': {
                'morning': '\u0938\u0941\u092a\u094d\u0930\u092d\u093e\u0924',
                'afternoon': '\u0928\u092e\u0938\u094d\u0915\u093e\u0930',
                'evening': '\u0936\u0941\u092d \u0938\u0902\u0927\u094d\u092f\u093e\u0915\u093e\u0933',
                'body': "{greeting}, {name}! \u092e\u0940 \u0924\u0941\u092e\u091a\u0940 \u0935\u0948\u092f\u0915\u094d\u0924\u093f\u0915 \u0915\u093e\u0933\u091c\u0940 \u0938\u0939\u093e\u092f\u094d\u092f\u0915 AVIRA \u0906\u0939\u0947\u0964 \u0924\u0941\u092e\u094d\u0939\u0940 \u092e\u0932\u093e \u0938\u0902\u0917\u0940\u0924, \u0935\u0947\u0933, \u0918\u0930\u0917\u0941\u0924\u0940 \u0909\u092a\u0915\u0930\u0923\u0947 \u0915\u093f\u0902\u0935\u093e \u0917\u092a\u094d\u092a\u093e \u092e\u093e\u0930\u0923\u094d\u092f\u093e\u0938\u093e\u0920\u0940 \u0935\u093f\u091a\u093e\u0930\u0942 \u0936\u0915\u0924\u093e\u0964 \u0924\u0941\u092e\u094d\u0939\u093e\u0932\u093e \u0915\u0927\u0940 \u0924\u093e\u0924\u094d\u0915\u093e\u0933 \u092e\u0926\u0924 \u0939\u0935\u0940 \u0905\u0938\u0932\u094d\u092f\u093e\u0938, '\u092e\u0926\u0924 \u0915\u0930\u093e' \u092c\u094b\u0932\u093e \u0915\u093f\u0902\u0935\u093e SOS \u092c\u091f\u0923 \u0926\u093e\u092c\u093e\u0964",
            },
        }

        logger.info("Initializing Elderly Care Assistant modules...")

        # Initialize all modules
        self.tts = TextToSpeechModule(
            rate=self.config["tts"]["rate"],
            volume=self.config["tts"]["volume"],
        )
        self.sr = SpeechRecognitionModule(
            language=self.config["speech"]["language"],
        )
        self.smart_home = SmartHomeModule(
            use_iot=self.config.get("iot", {}).get("enabled", True),
            esp32_ip=self.config.get("iot", {}).get("esp32_ip"),
            state_file="logs/device_states.json"
        )
        self.alerts = EmergencyAlertModule(
            user_name=self.config["user"]["name"],
            caregiver_contacts=self.config["emergency"]["contacts"],
            email_config=self.config["emergency"].get("email", {}),
        )
        self.commands = CommandProcessor(smart_home_module=self.smart_home)

        # Register smart home listener
        self.smart_home.add_listener(self._on_device_changed)

        logger.info("All modules initialized. Assistant ready.")

    def _default_config(self) -> dict:
        return {
            "user": {
                "name": "Friend",
                "age": 70,
            },
            "tts": {
                "rate": 140,
                "volume": 0.95,
            },
            "speech": {
                "language": "en-IN",
                "wake_word": "hey assistant",
            },
            "emergency": {
                "contacts": [
                    {
                        "name": "Primary Caregiver",
                        "phone": "+91-XXXXXXXXXX",
                        "email": "caregiver@example.com",
                        "relation": "Caregiver"
                    }
                ],
                "email": {}
            },
        }

    def greet(self):
        """Deliver startup greeting in the current language."""
        hour = datetime.datetime.now().hour
        lang = self._current_language
        templates = self._greetings.get(lang, self._greetings['en'])
        
        if hour < 12:
            greeting = templates['morning']
        elif hour < 17:
            greeting = templates['afternoon']
        else:
            greeting = templates['evening']

        name = self.config["user"]["name"]
        message = templates['body'].format(greeting=greeting, name=name)
        self.speak(message)
        return message

    def process_input(self, text: str, language: str = None) -> dict:
        """
        Process a text command from voice or typed input.
        Returns a full response context dict.
        """
        if not text or not text.strip():
            return {"response": "", "action": "empty_input", "success": False}

        # Use provided language or fall back to current setting
        lang = language or self._current_language

        text = text.lower().strip()
        logger.info(f"Processing input: '{text}' [lang={lang}]")

        # Store in conversation history
        self._conversation_history.append({
            "role": "user",
            "text": text,
            "timestamp": datetime.datetime.now().isoformat()
        })

        # Update last active timestamp
        self._last_active = datetime.datetime.now().isoformat()

        # Process command with language
        result = self.commands.process(text, language=lang, user_name=self.config["user"]["name"])
        emotion = result.get("emotion", "neutral")

        # Track emotion for caregiver dashboard
        self._emotion_history.append({
            "emotion": emotion,
            "text": text,
            "timestamp": datetime.datetime.now().isoformat(),
        })
        # Keep last 100 entries
        self._emotion_history = self._emotion_history[-100:]
        response = result.get("response", "I'm not sure I understood that.")

        # Handle special actions
        if result.get("trigger_sos"):
            sos_result = self.trigger_sos("voice")
            result["sos_result"] = sos_result
            response = (
                "Emergency alert triggered! I'm notifying your caregiver right now. "
                "Please stay calm. Help is coming."
            )

        if "smart_home_command" in result:
            cmd = result["smart_home_command"]
            if cmd and isinstance(cmd, list):
                # Helper function to execute a single command safely
                def execute_single_cmd(single_cmd):
                    if not isinstance(single_cmd, list):
                        return
                    
                    device_type = None
                    state = None
                    room = None
                    
                    if len(single_cmd) == 3:
                        device_type, state, room = single_cmd
                    elif len(single_cmd) == 2:
                        device_type, state = single_cmd
                    else:
                        logger.warning(f"Invalid smart home command format length: {single_cmd}")
                        return
                    
                    # Normalize room if it's 'all' or 'any' or empty
                    if isinstance(room, str):
                        room_clean = room.lower().strip()
                        if room_clean in ("all", "any", ""):
                            room = None
                            
                    try:
                        self.smart_home.set_device(device_type, state, room=room)
                        logger.info(f"Executed smart home command: type={device_type}, state={state}, room={room}")
                    except Exception as e:
                        logger.exception(f"Failed to execute smart home command {single_cmd}:")
                
                # Check if cmd is a list of lists or a single list
                if any(isinstance(x, list) for x in cmd):
                    # It's a list of lists, execute each command
                    for sub_cmd in cmd:
                        execute_single_cmd(sub_cmd)
                else:
                    # It's a single command list
                    execute_single_cmd(cmd)

        # Add emotion context to response for sad/anxious users (fallback if LLM not used)
        # Add emotion context to response for sad/anxious users (fallback if LLM not used)

        # Speak the response
        self.speak(response)

        # Store response in history
        self._conversation_history.append({
            "role": "assistant",
            "text": response,
            "emotion_detected": emotion,
            "action": result.get("action"),
            "timestamp": datetime.datetime.now().isoformat()
        })

        # Notify response callback (for GUI updates)
        if self._response_callback:
            try:
                self._response_callback(text, response, emotion, result)
            except Exception as e:
                logger.error(f"Response callback error: {e}")

        return {
            "user_input": text,
            "response": response,
            "emotion": emotion,
            "action": result.get("action"),
            "success": result.get("success", True),
            "language": lang,
            "extra": result,
        }

    def trigger_sos(self, trigger_type: str = "button") -> dict:
        """Trigger an emergency SOS alert."""
        logger.critical(f"SOS triggered via {trigger_type}")
        result = self.alerts.trigger_sos(
            trigger_type=trigger_type,
            location=f"{self.config['user']['name']}'s Home",
        )

        if self._sos_callback:
            try:
                self._sos_callback(result)
            except Exception as e:
                logger.error(f"SOS callback error: {e}")

        return result

    def speak(self, text: str, blocking: bool = False):
        """Speak text through TTS module."""
        self.tts.speak(text, blocking=blocking)

    def listen(self) -> str | None:
        """Listen for a single voice command."""
        return self.sr.listen_once()

    def start_listening_loop(self):
        """Start continuous voice interaction loop."""
        self.is_running = True
        self.greet()

        logger.info("Starting continuous listening loop...")
        while self.is_running:
            text = self.listen()
            if text:
                self.process_input(text)
            time.sleep(0.1)

    def stop(self):
        """Stop the assistant."""
        self.is_running = False
        self.sr.stop_continuous_listening()
        self.speak("Goodbye! I'll be here whenever you need me. Take care!")
        logger.info("Assistant stopped.")

    def _on_device_changed(self, device_id: str, device_data: dict):
        """Callback when a smart home device state changes."""
        if self._device_update_callback:
            try:
                self._device_update_callback(device_id, device_data)
            except Exception as e:
                logger.error(f"Device update callback error: {e}")

    def set_sos_callback(self, callback):
        """Set callback for SOS events."""
        self._sos_callback = callback

    def set_device_update_callback(self, callback):
        """Set callback for device state changes."""
        self._device_update_callback = callback

    def set_response_callback(self, callback):
        """Set callback for assistant responses."""
        self._response_callback = callback

    def get_full_status(self) -> dict:
        """Return comprehensive system status."""
        return {
            "assistant_running": self.is_running,
            "user": self.config["user"],
            "speech": self.sr.get_status(),
            "tts": self.tts.get_status(),
            "alerts": self.alerts.get_status(),
            "emotion": "active" if self.commands.emotion_classifier else "disabled",
            "conversation_turns": len(self._conversation_history) // 2,
        }

    def get_conversation_history(self, limit: int = 20) -> list:
        """Return recent conversation history."""
        return self._conversation_history[-limit * 2:]

    def consume_frontend_events(self) -> list:
        """Return and clear pending events specifically for the React frontend."""
        events = self._pending_frontend_events[:]
        self._pending_frontend_events.clear()
        return events

    def reset_session(self):
        """Clear all session data, history, and caregiver logs."""
        self._conversation_history = []
        self._caregiver_messages = []
        self._caregiver_sent_log = []
        self._reminders = []
        self._reminder_history = []
        self._emotion_history = []
        self._pending_frontend_events = []
        self.alerts._active = False
        self.alerts.alert_count = 0
        logger.info("Session state reset to default.")

    def set_language(self, lang: str):
        """Set the assistant's active language."""
        if lang in ('en', 'hi', 'mr'):
            self._current_language = lang
            logger.info(f"Language set to: {lang}")

    def get_language(self) -> str:
        """Return the current language code."""
        return self._current_language

    # ── Caregiver Features ──────────────────────────────────────────────────

    def queue_caregiver_message(self, text: str, from_name: str = "Caregiver") -> dict:
        """Queue a message from caregiver. AVIRA speaks it immediately."""
        msg = {
            "id": f"MSG-{datetime.datetime.now().strftime('%H%M%S')}-{len(self._caregiver_sent_log):03d}",
            "text": text,
            "from": from_name,
            "timestamp": datetime.datetime.now().isoformat(),
            "delivered": True,
        }
        # Speak it aloud immediately
        spoken = f"Message from {from_name}: {text}"
        self.speak(spoken)
        # Log in conversation history
        self._conversation_history.append({
            "role": "caregiver",
            "text": spoken,
            "timestamp": datetime.datetime.now().isoformat(),
        })
        self._caregiver_sent_log.append(msg)
        self._pending_frontend_events.append({
            "type": "CAREGIVER_MESSAGE", 
            "text": spoken, 
            "timestamp": datetime.datetime.now().isoformat()
        })
        logger.info(f"Caregiver message delivered: {text}")
        return msg

    def get_caregiver_sent_log(self) -> list:
        """Return all caregiver sent messages."""
        return self._caregiver_sent_log

    def add_reminder(self, text: str, time_str: str, repeat: str = "once") -> dict:
        """Add a scheduled reminder. time_str = 'HH:MM' (24h format)."""
        reminder = {
            "id": f"REM-{datetime.datetime.now().strftime('%H%M%S')}-{len(self._reminders):03d}",
            "text": text,
            "time": time_str,
            "repeat": repeat,  # 'once' or 'daily'
            "active": True,
            "created": datetime.datetime.now().isoformat(),
            "last_fired": None,
        }
        self._reminders.append(reminder)
        logger.info(f"Reminder added: '{text}' at {time_str} ({repeat})")
        # Start scheduler if not running
        self._start_reminder_scheduler()
        return reminder

    def get_reminders(self) -> list:
        """Return all reminders (active + inactive)."""
        return self._reminders

    def cancel_reminder(self, reminder_id: str) -> dict:
        """Cancel a reminder by ID."""
        for r in self._reminders:
            if r["id"] == reminder_id:
                r["active"] = False
                logger.info(f"Reminder cancelled: {reminder_id}")
                return {"success": True, "message": f"Reminder {reminder_id} cancelled."}
        return {"success": False, "message": f"Reminder {reminder_id} not found."}

    def get_emotion_history(self) -> list:
        """Return timestamped emotion predictions for charts."""
        return self._emotion_history

    def get_caregiver_dashboard(self) -> dict:
        """Return all data needed for caregiver dashboard."""
        # Count emotions today
        now = datetime.datetime.now()
        today_emotions = [e for e in self._emotion_history
                          if e["timestamp"][:10] == now.strftime("%Y-%m-%d")]
        emotion_counts = {}
        for e in today_emotions:
            em = e["emotion"]
            emotion_counts[em] = emotion_counts.get(em, 0) + 1

        # Mood alert: 3+ consecutive negative emotions
        negative = {"sadness", "anger", "fear"}
        recent = [e["emotion"] for e in self._emotion_history[-5:]]
        consecutive_negative = 0
        for em in reversed(recent):
            if em in negative:
                consecutive_negative += 1
            else:
                break
        mood_alert = consecutive_negative >= 3

        return {
            "user": self.config["user"],
            "last_active": self._last_active,
            "current_emotion": self._emotion_history[-1]["emotion"] if self._emotion_history else "neutral",
            "emotion_history": self._emotion_history[-20:],
            "emotion_counts": emotion_counts,
            "mood_alert": mood_alert,
            "mood_alert_count": consecutive_negative,
            "conversations_today": len([h for h in self._conversation_history
                                         if h["timestamp"][:10] == now.strftime("%Y-%m-%d")]),
            "sos_alerts": self.alerts.get_alert_history(),
            "sos_active": self.alerts._active,
            "devices": self.smart_home.get_all_devices(),
            "reminders": [r for r in self._reminders if r["active"]],
            "stats": {
                "total_conversations": len(self._conversation_history) // 2,
                "alerts_today": self.alerts.alert_count,
                "emotion_model": "active" if self.commands.emotion_classifier else "disabled",
            },
        }

    def _start_reminder_scheduler(self):
        """Start background thread to check reminders."""
        if self._reminder_thread and self._reminder_thread.is_alive():
            return
        self._reminder_thread = threading.Thread(target=self._reminder_loop, daemon=True)
        self._reminder_thread.start()
        logger.info("Reminder scheduler started.")

    def _reminder_loop(self):
        """Check reminders every 30 seconds."""
        while True:
            now = datetime.datetime.now()
            current_time = now.strftime("%H:%M")
            for r in self._reminders:
                if not r["active"]:
                    continue
                if r["time"] == current_time:
                    # Don't fire same reminder twice in same minute
                    if r["last_fired"] and r["last_fired"][:16] == now.isoformat()[:16]:
                        continue
                    # Fire the reminder
                    r["last_fired"] = now.isoformat()
                    spoken = f"Reminder: {r['text']}"
                    self.speak(spoken)
                    self._conversation_history.append({
                        "role": "reminder",
                        "text": spoken,
                        "timestamp": now.isoformat(),
                    })
                    self._reminder_history.append({**r, "fired_at": now.isoformat()})
                    self._pending_frontend_events.append({
                        "type": "REMINDER_TRIGGER", 
                        "text": spoken, 
                        "timestamp": now.isoformat()
                    })
                    logger.info(f"Reminder fired: {r['text']}")
                    if r["repeat"] == "once":
                        r["active"] = False
            time.sleep(30)


if __name__ == "__main__":
    # Console-only mode (no GUI)
    print("="*60)
    print("  ELDERLY CARE VOICE ASSISTANT - Phase 1 Prototype")
    print("="*60)
    print("Starting in console mode (no GUI)...")
    print("Type your commands, or say them if microphone is available.")
    print("Type 'quit' or 'exit' to stop.\n")

    assistant = ElderCareAssistant()
    assistant.greet()

    while True:
        try:
            user_input = input("\n[YOU]: ").strip()
            if user_input.lower() in ["quit", "exit", "bye"]:
                assistant.stop()
                break
            if user_input:
                result = assistant.process_input(user_input)
                print(f"[ASSISTANT]: {result['response']}")
                if result.get("emotion") != "neutral":
                    print(f"  [Emotion detected: {result['emotion']}]")
        except KeyboardInterrupt:
            assistant.stop()
            break
        except EOFError:
            break
