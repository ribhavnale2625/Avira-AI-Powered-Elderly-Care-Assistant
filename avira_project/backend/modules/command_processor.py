"""
Module 3: Command Processing & Task Execution
Interprets user voice commands and dispatches appropriate actions.
Handles: chit-chat.
"""

import logging
import os
import json
import socket
import webbrowser
import subprocess
import datetime
from dotenv import load_dotenv
import requests as http_requests
from .emotion_classifier import EmotionClassifier

logger = logging.getLogger(__name__)

dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=dotenv_path, override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

try:
    from groq import Groq
    if GROQ_API_KEY and GROQ_API_KEY != "YOUR_GROQ_API_KEY_HERE":
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("[INFO] Groq client successfully configured!")
    else:
        groq_client = None
        print("[WARNING] Groq API key not set.")
except Exception as e:
    groq_client = None
    logger.warning(f"Groq client failed to initialize: {e}")

# ── Ollama Configuration ────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")

def is_internet_available(timeout: float = 1.5) -> bool:
    """Quick check if internet connectivity is available via DNS lookup."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=timeout)
        return True
    except OSError:
        return False


class CommandProcessor:
    """
    Central command interpreter and task dispatcher.
    """

    def __init__(self, smart_home_module=None):
        self.smart_home = smart_home_module
        self.chat_history = []
        try:
            self.emotion_classifier = EmotionClassifier()
        except Exception as e:
            logger.error(f"Failed to load emotion classifier: {e}")
            self.emotion_classifier = None
        self._ollama_available = None  # cached check
        logger.info("CommandProcessor initialized")

    # Language display names for the Groq prompt
    LANG_NAMES = {
        "en": "English",
        "hi": "Hindi (हिन्दी)",
        "mr": "Marathi (मराठी)",
    }

    def process(self, text: str, emotion: str = "neutral", language: str = "en", user_name: str = None) -> dict:
        """
        Process a text command and return a result dict with:
        - response: str (what assistant should say)
        - action: str (what was done)
        - success: bool
        - language: str (response language)
        """
        text = text.lower().strip()
        logger.info(f"Processing command: '{text}' [lang={language}]")

        # Force neutral emotion for any smart home queries (commands or status questions)
        is_smart_home_query = False
        smart_home_nouns = {
            "light", "lights", "bulb", "led", "lamp", "fan", "fans", "tv", "television", "lock", "door", "buzzer", "ac", "air conditioner",
            "लाइट", "लाइटें", "लाईट", "लाईट्स", "दिवा", "दिवे", "पंखा", "पंखे", "फॅन", "टीव्ही", "टीवी", "दरवाजा", "दार", "लॉक", "कुलूप"
        }
        
        has_noun = any(noun in text for noun in smart_home_nouns) or "air conditioner" in text
        if has_noun:
            is_smart_home_query = True
            logger.info("Smart home query pattern detected. Bypassing emotion detection, setting to neutral.")

        # Detect emotion if possible
        detected_emotion = "neutral"
        if not is_smart_home_query and self.emotion_classifier:
            try:
                detected_emotion = self.emotion_classifier.predict(text)
                logger.info(f"Detected emotion: {detected_emotion}")
            except Exception as e:
                logger.error(f"Emotion prediction error: {e}")

        # Get device states to inject into prompt
        device_states_str = ""
        if self.smart_home:
            states = []
            for dev_id, dev in self.smart_home.get_all_devices().items():
                status_str = "ON" if dev["state"] else "OFF"
                if dev["type"] == "lock":
                    status_str = "LOCKED" if dev["state"] else "UNLOCKED"
                states.append(f"- {dev['name']} ({dev['room']}): {status_str}")
            device_states_str = "\n".join(states)

        # 1. Handle deterministic tasks (open apps/websites, date, time)
        task_result = self._handle_tasks(text, language, user_name)
        if task_result:
            task_result["emotion"] = detected_emotion
            task_result["language"] = language
            return task_result

        # 2. Directly handle chitchat if no task matched
        result = self._handle_chitchat(
            text=text, 
            language=language, 
            emotion=detected_emotion, 
            user_name=user_name, 
            is_smart_home_query=is_smart_home_query,
            device_states_str=device_states_str
        )
        if result:
            result["emotion"] = detected_emotion
            result["language"] = language
            return result

        return {
            "response": "I'm sorry, my AI connection seems to be offline.",
            "action": "chitchat_fallback",
            "success": False,
        }

    # ─── Ollama Local LLM Call ──────────────────────────────────────────────────
    def _call_ollama(self, messages: list) -> str | None:
        """Send messages to local Ollama API and return raw response content."""
        try:
            payload = {
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "format": "json",
                "options": {
                    "num_predict": 400,
                    "temperature": 0.7,
                }
            }
            resp = http_requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data.get("message", {}).get("content", "")
            logger.info(f"Ollama response content: {repr(content)}")
            return content
        except Exception as e:
            logger.exception(f"Ollama API error: {e}")
            return None

    def _handle_chitchat(self, text: str, language: str = "en", emotion: str = "neutral", user_name: str = None, is_smart_home_query: bool = False, device_states_str: str = "") -> dict | None:
        # ── Get current time for system prompt ────────────────────────────────
        now = datetime.datetime.now()
        current_time_str = now.strftime("%I:%M %p")
        current_date_str = now.strftime("%A, %B %d, %Y")

        # ── Build the system prompt (shared by both Groq and Ollama) ──────────
        lang_name = self.LANG_NAMES.get(language, "English")
        lang_instruction = ""
        
        # Format name if it is not default 'Friend' or 'User'
        has_custom_name = user_name and user_name.strip() not in ("", "Friend", "User", "friend", "user")
        
        if language == "hi":
            if has_custom_name:
                name_address = f"Address them respectfully by their configured name '{user_name} ji' (जैसे '{user_name} जी')."
            else:
                name_address = "Address them respectfully and politely without using a specific name, and NEVER use familial/relationship titles like 'Dada-ji', 'Dadi-ji', or 'Kaku'."
            
            lang_instruction = (
                "CRITICAL LANGUAGE RULE: You MUST respond ONLY in Hindi (हिन्दी). "
                "Avoid mechanical translation. Use natural, warm phrasing. "
                "Use polite and respectful 'Aap' (आप) always for the user. "
                f"{name_address} "
                "Do NOT use familial/relationship titles under any circumstances. "
                "Only if appropriate for general chitchat, you can sprinkle in comforting, polite phrases like: 'बिल्कुल चिंता न करें', 'मैं हूँ न'. Do NOT use these for device commands. "
                "Write English technical terms like 'YouTube', 'Light', 'Fan' phonetically: 'यूट्यूब', 'लाइट', 'पंखा'. "
                "Use proper Devanagari punctuation to ensure the TTS has natural pauses and a caring rhythm. "
            )
        elif language == "mr":
            if has_custom_name:
                name_address = f"Address them respectfully using their name '{user_name}'."
            else:
                name_address = "Address them respectfully and politely without using a specific name, and NEVER use familial/relationship titles like 'Aajo-ba', 'Aaji', or 'Kaka/Kaku'."
            
            lang_instruction = (
                "CRITICAL LANGUAGE RULE: You MUST respond ONLY in Marathi (मराठी). "
                "Use pure, respectful Marathi. Avoid 'Hinglish'. "
                f"{name_address} "
                "Do NOT use familial/relationship titles under any circumstances. "
                "Use the respectful 'Tumhi' (तुम्ही) and 'Aapan' (आपण). "
                "Only if appropriate for general chitchat, you can use comforting phrases like: 'काळजी घ्या बरं का', 'मी तुमची मदत करायला इथेच आहे'. Do NOT use these for device commands. "
                "Ensure English words are phonetic: 'यूट्यूब', 'टीव्ही', 'लाईट'. "
                "Maintain a gentle, polite, and caring tone, but do not assume family relationships."
            )
        else:
            if has_custom_name:
                name_address = f"Address the user by their name '{user_name}'."
            else:
                name_address = "Address the user politely without using any specific name, and NEVER use familial or relationship titles (such as Dada, Dadi, Kaka, Kaku, dear, beloved grandparent, etc.)."
            
            lang_instruction = (
                "Respond in warm, clear, and soothing English. Use a gentle, caring, and professional tone. "
                f"{name_address} "
                "Do NOT use familial or relationship titles under any circumstances. "
                "Do not assume family relationships or make claims of long-term familiarity. Keep the tone helpful, reassuring, and respectful."
            )

        system_prompt = (
            "You are AVIRA, a warm, polite, and respectful digital voice assistant designed for elderly care. "
            "Your primary goal is to make the user feel safe, heard, and respected, while maintaining a professional and non-creepy boundaries. "
            "PERSONALITY RULES:\n"
            "- Speak gently and at a relaxed pace (not slow, but never rushed).\n"
            "- Use empathetic active listening: acknowledge their feelings before answering when they are sharing emotions during general chitchat.\n"
            "- SMART HOME / DEVICE COMMANDS: If the user's input is a command to control devices, keep your response completely dry, direct, and concise (e.g., 'Sure, turning on the lights.' or 'I have turned on the fan.'). Do NOT include any emotional analysis, friendly check-ins, or well-being questions. The response MUST be a single, short confirmation sentence and MUST NOT be empty.\n"
            "- SMART HOME STATUS QUERIES: If the user is asking about device status, answer the question directly and briefly using the current device states listed below. Do not try to toggle or command the device unless they asked to change it (set 'smart_home_command' to null).\n"
            "- Do NOT use gentle endearments or familial titles (Dada, Dadi, Kaka, Kaku, dear, beloved grandparent, etc.) under any circumstances. Keep the tone respectful and polite.\n"
            "- Do NOT proactively check in on well-being or ask 'How are you feeling?' or 'Did you have your tea?' for device control commands or other non-chitchat interactions.\n"
            "- Use a conversational, natural tone — avoid 'As an AI' or robotic phrasing.\n"
            "- Do not claim long-term familiarity or say creepy/presumptuous things like 'Don't you remember me?'.\n"
            f"- CURRENT TIME AND DATE: The current local time is {current_time_str} and the date is {current_date_str}. Use this exact time and date to answer any questions about the current time or date. Do not guess or make up the time.\n"
            "- PHYSICAL LIMITATIONS & BOUNDARIES: You are a digital, online assistant. You can only help emotionally, conversationally, and digitally. You CANNOT perform physical tasks like making dinner, brewing coffee, fetching physical objects, cooking, cleaning, or doing chores. If the user asks for physical help, politely and clearly explain this limitation, then offer to help with a digital or emotional alternative instead.\n"
            "- Length: Keep it brief and concise. 1 to 3 natural, flowing sentences is ideal. Do not drag out the response or make it overly long.\n"
            "CULTURAL FLUENCY:\n"
            "- For Hindi/Marathi, use idioms and phrasing that feel native, not translated.\n"
            f"{lang_instruction}\n"
            f"The user is currently feeling: {emotion.upper()}. Adjust your warmth and empathy to match this mood, but prioritize command execution over mood matching.\n"
            "OUTPUT FORMAT: You MUST return a JSON object with exactly these keys:\n"
            "1. 'response': Your spoken response. (No asterisks or markdown).\n"
            "2. 'smart_home_command': A list representing a single command, or a list of multiple command lists (to control multiple devices), OR null. "
            "Valid single command formats: ['light', true/false, 'room'], ['fan', true/false, 'room'], ['tv', true/false, 'room'], ['lock', true/false]. "
            "If controlling multiple devices (e.g. 'turn on all the lights'), use a list of lists: [['light', true, 'Living Room'], ['light', true, 'Bedroom']]. "
            "CRITICAL: Never output duplicate keys in the JSON response. Always put all commands in a single list under the 'smart_home_command' key.\n"
            "3. 'web_url': A string URL if the user wants to see something (e.g. 'open netflix', 'show me news', 'play bhajans', 'go to youtube'), otherwise null.\n"
            "Example: {\"response\": \"Of course, I can help you watch some movies. I am opening Netflix for you now.\", \"web_url\": \"https://www.netflix.com\", \"smart_home_command\": null}"
        )

        if is_smart_home_query:
            words_in_text = set(text.split())
            is_query = "?" in text or any(w in words_in_text for w in {"is", "are", "status", "check", "whether"})
            is_command = not is_query
            
            if is_command:
                if language == "hi":
                    example_str = "जी, लाइट चालू कर देती हूँ।"
                elif language == "mr":
                    example_str = "हो, लाईट चालू करते."
                else:
                    example_str = "Sure, turning on the lights."
                
                system_prompt += (
                    f"\nIMPORTANT DIRECTIVE: The user's input is a direct device control command. "
                    f"You MUST respond ONLY in {lang_name} with a single, short, direct sentence confirming the action "
                    f"(e.g., '{example_str}'). "
                    f"Do NOT include any greeting, emotional check-in, well-being question, or empathetic analysis. "
                    f"The 'response' field in your JSON output MUST contain this confirmation sentence and MUST NOT be empty."
                )
            else:
                system_prompt += (
                    f"\nIMPORTANT DIRECTIVE: The user is asking a status query about smart home devices. "
                    f"Answer the question directly and briefly ONLY in {lang_name} using the current states listed below. "
                    f"Do NOT try to change the state of the device, and set the 'smart_home_command' field to null. "
                    f"Do NOT include any emotional check-ins, well-being questions, or empathetic analysis. "
                    f"Keep the response direct and short."
                )
            
            if device_states_str:
                system_prompt += f"\n\nCURRENT SMART HOME DEVICE STATES:\n{device_states_str}\n"

        # ── Build message list ───────────────────────────────────────────────
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.chat_history[-10:])
        messages.append({"role": "user", "content": text})

        raw_content = None
        used_backend = None

        # ── Strategy 1: Try Groq (online) ────────────────────────────────────
        if groq_client is not None and is_internet_available():
            try:
                logger.info("Internet available — using Groq API.")
                response = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=messages,
                    max_tokens=400,
                    response_format={"type": "json_object"}
                )
                raw_content = response.choices[0].message.content
                used_backend = "groq"
                logger.info(f"Groq response content: {repr(raw_content)}")
            except Exception as e:
                logger.error(f"Groq API call failed: {e}")
                raw_content = None

        if raw_content is None:
            # Inform the user that the online brain (Groq) is currently unavailable
            error_msg = {
                "en": "I'm sorry, my online brain (Groq) is currently unavailable or internet is disconnected.",
                "hi": "मुझे खेद है, मेरा ऑनलाइन मस्तिष्क (Groq) अभी अनुपलब्ध है या इंटरनेट बंद है।",
                "mr": "मला दिलगीर आहे, माझे ऑनलाइन मेंदू (Groq) सध्या उपलब्ध नाही किंवा इंटरनेट बंद आहे।"
            }
            return {
                "response": error_msg.get(language, error_msg["en"]),
                "action": "chitchat_error",
                "success": False,
            }

        # ── Parse the JSON response (same for both backends) ─────────────────
        try:
            data = json.loads(raw_content)
            speech = data.get("response", "I'm not exactly sure about that, but I'm here for you!")
            sh_cmd = data.get("smart_home_command")
            web_url = data.get("web_url")
        except json.JSONDecodeError:
            speech = raw_content.strip() if raw_content.strip() else "I'm sorry, I got a bit confused just now."
            sh_cmd = None
            web_url = None

        self.chat_history.append({"role": "user", "content": text})
        self.chat_history.append({"role": "assistant", "content": speech})

        res_dict = {
            "response": speech.replace('*', '').strip(),
            "action": "chitchat_ai",
            "success": True,
            "backend": used_backend,
        }
        if sh_cmd and isinstance(sh_cmd, list):
            res_dict["smart_home_command"] = sh_cmd
        if web_url and isinstance(web_url, str):
            res_dict["url"] = web_url
            # Try to open it on server too just in case
            try: webbrowser.open(web_url)
            except: pass
        return res_dict

    # ─── Task Execution ────────────────────────────────────────────────────────
    def _handle_tasks(self, text: str, language: str = "en", user_name: str = None) -> dict | None:
        """
        Recognizes and executes deterministic tasks (opening websites/apps, date, time).
        """
        t = text.lower()

        # Localization dictionary for days and months in Hindi and Marathi
        DAYS_HI = {
            "Monday": "सोमवार", "Tuesday": "मंगलवार", "Wednesday": "बुधवार",
            "Thursday": "गुरुवार", "Friday": "शुक्रवार", "Saturday": "शनिवार", "Sunday": "रविवार"
        }
        DAYS_MR = {
            "Monday": "सोमवार", "Tuesday": "मंगळवार", "Wednesday": "बुधवार",
            "Thursday": "गुरुवार", "Friday": "शुक्रवार", "Saturday": "शनिवार", "Sunday": "रविवार"
        }
        MONTHS_HI = {
            "January": "जनवरी", "February": "फ़रवरी", "March": "मार्च", "April": "अप्रैल",
            "May": "मई", "June": "जून", "July": "जुलाई", "August": "अगस्त",
            "September": "सितंबर", "October": "अक्टूबर", "November": "नवंबर", "December": "दिसंबर"
        }
        MONTHS_MR = {
            "January": "जानेवारी", "February": "फेब्रुवारी", "March": "मार्च", "April": "एप्रिल",
            "May": "मे", "June": "जून", "July": "जुलै", "August": "ऑगस्ट",
            "September": "सप्टेंबर", "October": "ऑक्टोबर", "November": "नोव्हेंबर", "December": "डिसेंबर"
        }

        # Check for Time Query
        time_keywords_en = ["what time is it", "what is the time", "what's the time", "tell me the time", "current time", "time please"]
        time_keywords_hi = ["समय क्या हुआ", "कितने बजे", "समय बताओ", "वक्त क्या हुआ", "टाइम क्या है", "समय क्या है"]
        time_keywords_mr = ["वेळ काय झाली", "किती वाजले", "वेळ सांग", "टाईम काय झाला", "वेळ काय आहे"]

        is_time_query = False
        if any(w in t for w in time_keywords_en):
            is_time_query = True
        elif any(w in t for w in time_keywords_hi):
            is_time_query = True
        elif any(w in t for w in time_keywords_mr):
            is_time_query = True
        elif len(t.split()) <= 4 and any(w in t for w in ["time", "समय", "वेळ", "टाइम", "टाईम", "वक्त"]):
            if not any(w in t for w in ["reminder", "remind", "set", "alarm", "रिमाइंडर"]):
                is_time_query = True

        # Check for Date Query
        date_keywords_en = ["what is the date", "what's the date", "today's date", "what is today's date", "date please", "what day is it", "what is the day today", "what's today's date"]
        date_keywords_hi = ["आज क्या तारीख है", "आज कौन सा दिन है", "तारीख बताओ", "दिनांक क्या है", "आज की तारीख"]
        date_keywords_mr = ["आज कोणती तारीख आहे", "आज कोणता दिवस आहे", "तारीख सांग", "दिनांक सांग", "आजची तारीख"]

        is_date_query = False
        if any(w in t for w in date_keywords_en):
            is_date_query = True
        elif any(w in t for w in date_keywords_hi):
            is_date_query = True
        elif any(w in t for w in date_keywords_mr):
            is_date_query = True
        elif len(t.split()) <= 4 and any(w in t for w in ["date", "day", "तारीख", "दिनांक", "दिवस", "वार"]):
            if not any(w in t for w in ["reminder", "remind", "set", "alarm", "रिमाइंडर"]):
                is_date_query = True

        if is_time_query or is_date_query:
            name_suffix = ""
            if user_name and user_name.strip() not in ("", "Friend", "User", "friend", "user"):
                if language == "hi":
                    name_suffix = f", {user_name} जी"
                elif language == "mr":
                    name_suffix = f", {user_name}"
                else:
                    name_suffix = f", {user_name}"

            if is_time_query:
                url = "https://www.google.com/search?q=current+time"
                try:
                    webbrowser.open(url)
                except Exception as e:
                    logger.error(f"Failed to open Google for time: {e}")

                if language == "hi":
                    response = f"मैं आपके लिए गूगल पर सही समय खोल रही हूँ{name_suffix}।"
                elif language == "mr":
                    response = f"मी तुमच्यासाठी गुगलवर चालू वेळ उघडत आहे{name_suffix}।"
                else:
                    response = f"I am opening Google to show you the current time{name_suffix}."
                
                return {
                    "response": response,
                    "action": "get_time",
                    "url": url,
                    "success": True
                }

            if is_date_query:
                url = "https://www.google.com/search?q=current+date"
                try:
                    webbrowser.open(url)
                except Exception as e:
                    logger.error(f"Failed to open Google for date: {e}")

                if language == "hi":
                    response = f"मैं आपके लिए गूगल पर आज की तारीख खोल रही हूँ{name_suffix}।"
                elif language == "mr":
                    response = f"मी तुमच्यासाठी गुगलवर आजची तारीख उघडत आहे{name_suffix}।"
                else:
                    response = f"I am opening Google to show you the current date{name_suffix}."

                return {
                    "response": response,
                    "action": "get_date",
                    "url": url,
                    "success": True
                }
        logger.info(f"Task detection on: '{t}'")
        
        # Mapping keywords to URLs
        SITES = {
            "youtube": "https://www.youtube.com",
            "google": "https://www.google.com",
            "facebook": "https://www.facebook.com",
            "instagram": "https://www.instagram.com",
            "netflix": "https://www.netflix.com",
            "prime": "https://www.amazon.com/Prime-Video",
            "whatsapp": "https://web.whatsapp.com",
            "news": "https://news.google.com",
            "weather": "https://www.weather.com",
            "gmail": "https://mail.google.com"
        }
        
        APPS = {
            "calculator": "calc",
            "notepad": "notepad",
            "paint": "mspaint",
            "control panel": "control",
            "settings": "start ms-settings:",
            "browser": "start chrome", # Fallback to chrome if available
            "explorer": "explorer",
            "task manager": "taskmgr",
        }

        # Check for Website Opening
        for site, url in SITES.items():
            # Match "open youtube", "go to youtube", "launch youtube"
            if any(cmd in t for cmd in ["open", "go to", "launch", "show me"]) and site in t:
                try:
                    logger.info(f"Attempting to open website: {site} -> {url}")
                    # Try opening via backend
                    webbrowser.open(url)
                    
                    msg = {
                        "en": f"Of course! I'm opening {site.capitalize()} for you right now.",
                        "hi": f"जी, मैं आपके लिए {site.capitalize()} अभी खोल देती हूँ।",
                        "mr": f"हो, नक्कीच! मी तुमच्यासाठी {site.capitalize()} आत्ताच उघडत आहे।"
                    }
                    return {
                        "response": msg.get(language, msg["en"]),
                        "action": f"open_site_{site}",
                        "url": url, # Pass URL for frontend backup
                        "success": True
                    }
                except Exception as e:
                    logger.error(f"Failed to open site {site}: {e}")

        # Check for App Opening
        for app, cmd in APPS.items():
            if any(cmd_word in t for cmd_word in ["open", "launch", "start", "run"]) and app in t:
                try:
                    logger.info(f"Attempting to open app: {app} -> {cmd}")
                    # Use start command for better Windows app handling
                    if os.name == 'nt':
                        subprocess.Popen(f"start {cmd}" if not cmd.startswith("start") else cmd, shell=True)
                    else:
                        subprocess.Popen(cmd, shell=True)

                    msg = {
                        "en": f"Sure thing! I'm opening the {app.capitalize()} app for you.",
                        "hi": f"जी, मैं आपके लिए {app.capitalize()} अभी शुरू कर रही हूँ।",
                        "mr": f"हो, मी तुमच्यासाठी {app.capitalize()} ॲप आत्ताच सुरू करत आहे।"
                    }
                    return {
                        "response": msg.get(language, msg["en"]),
                        "action": f"open_app_{app}",
                        "success": True
                    }
                except Exception as e:
                    logger.error(f"Failed to app {app}: {e}")

        # Music handling
        if any(w in t for w in ["play", "start", "listen to", "music", "song", "bhajan", "ghazal", "गाणे", "गीत", "भजन"]):
            if any(w in t for w in ["music", "song", "bhajan", "ghazal", "relaxing", "गाणे", "गीत", "भजन"]):
                query = "relaxing+music+for+seniors"
                if "hindi" in t or "bollywood" in t or "पुराने" in t:
                    query = "old+hindi+songs+70s+80s+evergreen"
                elif "marathi" in t or "मराठी" in t:
                    query = "marathi+old+classic+songs+bhakti+geet"
                elif "classical" in t or "शास्त्रीय" in t:
                    query = "indian+classical+music+instrumental+soothing"
                
                url = f"https://www.youtube.com/results?search_query={query}"
                
                try:
                    logger.info(f"Playing music with query: {query}")
                    webbrowser.open(url)
                    msg = {
                        "en": "I've found some relaxing music for you on YouTube. I hope you enjoy it!",
                        "hi": "मैंने आपके लिए यूट्यूब पर कुछ संगीत ढूँढा है। आशा है आपको पसंद आएगा।",
                        "mr": "मी तुमच्यासाठी यूट्यूबवर संगीत शोधले आहे। तुम्हाला ते आवडेल अशी आशा आहे।"
                    }
                    return {
                        "response": msg.get(language, msg["en"]),
                        "action": "play_music",
                        "url": url,
                        "success": True
                    }
                except Exception as e:
                    logger.error(f"Failed to play music: {e}")

        return None
