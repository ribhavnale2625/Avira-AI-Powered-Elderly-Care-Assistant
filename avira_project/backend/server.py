"""
AVIRA – Elderly Care Voice Assistant
Flask API Server — bridges the Python backend modules to the React frontend.

DEBUG FIXED:
 - UnicodeEncodeError: Replaced icons (✗ ✓ 🚨) with ASCII [X] [OK] [SOS] 
 - Deprecated google.generativeai warning suppressed 
 - Added UTF-8 logging, threaded server for better concurrency

Endpoints:
  POST /api/process      – Process a text command (full pipeline)
  POST /api/sos/trigger  – Trigger emergency SOS alert
  POST /api/sos/cancel   – Cancel active SOS alert
  GET  /api/devices      – Get all smart home device states
  POST /api/devices/<id>/toggle  – Toggle a device
  POST /api/devices/<id>/set     – Set device properties
  GET  /api/status       – Get full system status
  GET  /api/history      – Get conversation history

Usage:
  pip install -r requirements.txt flask flask-cors
  python server_fixed.py
  Then open the React frontend at http://localhost:5173
"""

import os
import sys
import json
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from flask import Flask, request, jsonify
from flask_cors import CORS

# Windows UTF-8 console
if os.name == 'nt':
    os.system('chcp 65001 >nul')

# Ensure the backend package is importable
sys.path.insert(0, os.path.dirname(__file__))

from assistant import ElderCareAssistant
from caregiver_routes import caregiver_bp, init_caregiver
from modules.face_emotion_module import FaceEmotionDetector

# ── Logging (UTF-8 safe) ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/server.log", encoding='utf-8')
    ]
)
logger = logging.getLogger("AVIRA-Server")

# ── Flask App ────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, origins="*")  # Allow all origins for caregiver PWA access

# ── ESP32 Configuration ─────────────────────────────────────────────────────
ESP32_IP = os.environ.get("ESP32_IP", "192.168.1.100")

# ── Initialise assistant ────────────────────────────────────────────────────
CONFIG = {
    "user": {"name": "Ribhav", "age": 72},
    "tts":  {"rate": 140, "volume": 0.95},
    "speech": {"language": "en-IN"},
    "emergency": {
        "contacts": [
            {"name": "Primary Caregiver", "phone": "+91-XXXXXXXXXX",
             "email": "caregiver@example.com", "relation": "Caregiver"}
        ],
        "email": {}   # Fill in for real email alerts
    },
    "iot": {
        "enabled": True,
        "esp32_ip": ESP32_IP,
    },
}

try:
    assistant = ElderCareAssistant(config=CONFIG)
    init_caregiver(assistant)
    app.register_blueprint(caregiver_bp)
    logger.info("AVIRA assistant initialised successfully (debug fixed).")
    logger.info("Caregiver portal registered at /caregiver")
except Exception as e:
    logger.error(f"Failed to initialize assistant: {e}")
    sys.exit(1)

# ── Face Emotion Detector (lazy-loaded, won't block startup) ────────────────
face_detector = FaceEmotionDetector()

# ── Routes ──────────────────────────────────────────────────────────────────

@app.route("/api/process", methods=["POST"])
def process_command():
    """Process a text command through the full assistant pipeline."""
    try:
        data = request.get_json(force=True)
        text = data.get("text", "").strip()
        language = data.get("language", "en")
        if not text:
            return jsonify({"error": "No text provided"}), 400

        result = assistant.process_input(text, language=language)
        extra = result.get("extra", {}) or {}
        return jsonify({
            "response":  result.get("response", ""),
            "emotion":   result.get("emotion", "neutral"),
            "action":    result.get("action", ""),
            "url":       extra.get("url"), # Critical for opening tabs in frontend
            "smart_home_command": extra.get("smart_home_command"), # For UI status
            "success":   result.get("success", True),
            "language":  result.get("language", language),
            "backend":   extra.get("backend"),  # 'groq' or 'ollama'
        })
    except Exception as e:
        logger.error(f"/api/process error: {e}")
        return jsonify({"error": "Processing failed", "details": str(e)}), 500


@app.route("/api/sos/trigger", methods=["POST"])
def trigger_sos():
    """Trigger an emergency SOS alert + forward to ESP32 for offline buzzer/LED."""
    try:
        data         = request.get_json(force=True) or {}
        trigger_type = data.get("trigger_type", "button")
        result       = assistant.trigger_sos(trigger_type)
        # Also trigger offline SOS on ESP32 (buzzer + LED flash)
        esp32_result = assistant.smart_home.trigger_sos_on_esp32()
        result["esp32_sos"] = esp32_result
        return jsonify(result)
    except Exception as e:
        logger.error(f"SOS trigger error: {e}")
        return jsonify({"error": "SOS failed", "details": str(e)}), 500


@app.route("/api/sos/cancel", methods=["POST"])
def cancel_sos():
    """Cancel the active SOS alert + cancel on ESP32."""
    try:
        result = assistant.alerts.cancel_alert()
        esp32_result = assistant.smart_home.cancel_sos_on_esp32()
        result["esp32_sos"] = esp32_result
        return jsonify(result)
    except Exception as e:
        logger.error(f"SOS cancel error: {e}")
        return jsonify({"error": "Cancel failed", "details": str(e)}), 500


@app.route("/api/devices", methods=["GET"])
def get_devices():
    """Return all smart home device states."""
    try:
        return jsonify(assistant.smart_home.get_all_devices())
    except Exception as e:
        logger.error(f"Devices error: {e}")
        return jsonify({"error": "Devices fetch failed"}), 500


@app.route("/api/devices/<device_id>/toggle", methods=["POST"])
def toggle_device(device_id: str):
    """Toggle a device on/off."""
    try:
        result = assistant.smart_home.toggle_device(device_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Toggle {device_id} error: {e}")
        return jsonify({"error": "Toggle failed"}), 500


@app.route("/api/devices/<device_id>/set", methods=["POST"])
def set_device(device_id: str):
    """Set specific device properties (brightness, speed, etc.)."""
    try:
        data       = request.get_json(force=True) or {}
        device     = assistant.smart_home.get_device_state(device_id)
        if not device:
            return jsonify({"error": f"Device '{device_id}' not found"}), 404

        state      = data.get("state", device["state"])
        extra      = {k: v for k, v in data.items() if k not in ("state",)}
        result     = assistant.smart_home.set_device_by_id(device_id, state=state, **extra)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Set device {device_id} error: {e}")
        return jsonify({"error": "Set failed"}), 500


@app.route("/api/status", methods=["GET"])
def get_status():
    """Return full system status."""
    try:
        return jsonify(assistant.get_full_status())
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({"error": "Status fetch failed"}), 500


@app.route("/api/history", methods=["GET"])
def get_history():
    """Return recent conversation history."""
    try:
        limit   = int(request.args.get("limit", 20))
        history = assistant.get_conversation_history(limit)
        return jsonify(history)
    except Exception as e:
        logger.error(f"History error: {e}")
        return jsonify({"error": "History fetch failed"}), 500


@app.route("/api/system/reset-session", methods=["POST"])
def reset_session():
    """Reset the assistant session state when the frontend is refreshed."""
    try:
        assistant.reset_session()
        return jsonify({"success": True, "message": "Session reset successfully"}), 200
    except Exception as e:
        logger.error(f"Reset session error: {e}")
        return jsonify({"error": "Reset session failed"}), 500


@app.route("/api/home/summary", methods=["GET"])
def home_summary():
    """Return a human-readable home status summary."""
    try:
        return jsonify({"summary": assistant.smart_home.get_home_summary()})
    except Exception as e:
        logger.error(f"Home summary error: {e}")
        return jsonify({"error": "Summary failed"}), 500


@app.route("/api/esp32/status", methods=["GET"])
def esp32_status():
    """Check ESP32 connectivity and return status."""
    try:
        return jsonify(assistant.smart_home.get_esp32_status())
    except Exception as e:
        logger.error(f"ESP32 status error: {e}")
        return jsonify({"error": "ESP32 status failed"}), 500


@app.route("/api/esp32/sync", methods=["POST"])
def esp32_sync():
    """Sync device states from ESP32 hardware."""
    try:
        result = assistant.smart_home.sync_from_esp32()
        return jsonify(result)
    except Exception as e:
        logger.error(f"ESP32 sync error: {e}")
        return jsonify({"error": "ESP32 sync failed"}), 500


@app.route("/api/esp32/register", methods=["POST"])
def register_esp32():
    """Register ESP32 dynamically based on role (home_automation or fall_detection)."""
    try:
        data = request.get_json(force=True) or {}
        role = data.get("role")
        ip = data.get("ip")
        if not role or not ip:
            return jsonify({"error": "Role and IP must be provided"}), 400
        
        if role == "home_automation":
            assistant.smart_home.update_esp32_ip(ip)
        elif role == "fall_detection":
            assistant.smart_home.fall_detection_ip = ip
            logger.info(f"Registered Gyro Fall Detection ESP32 IP: {ip}")
        else:
            return jsonify({"error": f"Invalid role: {role}"}), 400
            
        return jsonify({
            "success": True,
            "message": f"Successfully registered {role} at {ip}",
            "home_automation_ip": assistant.smart_home.esp32_ip,
            "fall_detection_ip": assistant.smart_home.fall_detection_ip
        }), 200
    except Exception as e:
        logger.error(f"ESP32 registration error: {e}")
        return jsonify({"error": "Registration failed", "details": str(e)}), 500


@app.route("/api/languages", methods=["GET"])
def get_languages():
    """Return supported languages."""
    return jsonify({
        "languages": [
            {"code": "en", "name": "English",  "nativeName": "English"},
            {"code": "hi", "name": "Hindi",    "nativeName": "\u0939\u093f\u0928\u094d\u0926\u0940"},
            {"code": "mr", "name": "Marathi",  "nativeName": "\u092e\u0930\u093e\u0920\u0940"},
        ],
        "current": assistant.get_language(),
    })


@app.route("/api/set-language", methods=["POST"])
def set_language():
    """Set the assistant's active language."""
    try:
        data = request.get_json(force=True)
        lang = data.get("language", "en")
        if lang not in ("en", "hi", "mr"):
            return jsonify({"error": f"Unsupported language: {lang}"}), 400
        assistant.set_language(lang)
        return jsonify({"success": True, "language": lang})
    except Exception as e:
        logger.error(f"Set language error: {e}")
        return jsonify({"error": "Set language failed"}), 500

@app.route("/api/face-emotion", methods=["POST"])
def face_emotion():
    """Detect emotion from a webcam frame (base64 JPEG) using FER-2013 CNN."""
    import base64
    try:
        data = request.get_json(force=True)
        image_b64 = data.get("image", "")
        if not image_b64:
            return jsonify({"error": "No image provided"}), 400

        # Strip data URL prefix if present (e.g. "data:image/jpeg;base64,...")
        if "," in image_b64:
            image_b64 = image_b64.split(",", 1)[1]

        image_bytes = base64.b64decode(image_b64)
        result = face_detector.detect(image_bytes)

        # Store in assistant emotion history if face detected
        if result.get("face_detected") and result.get("confidence", 0) > 40:
            import datetime
            assistant._emotion_history.append({
                "timestamp": datetime.datetime.now().isoformat(),
                "source": "face",
                "emotion": result["emotion"],
                "confidence": result["confidence"],
            })

        return jsonify(result)

    except Exception as e:
        logger.error(f"Face emotion error: {e}")
        return jsonify({"error": "Face emotion detection failed", "details": str(e)}), 500


@app.route("/api/tts", methods=["POST"])
def text_to_speech():
    """Convert text to speech using OpenAI TTS (tts-1-hd, alloy voice, speed 1.15)."""
    import base64
    try:
        data = request.get_json(force=True)
        text = data.get("text", "").strip()
        language = data.get("language", "en")
        if not text:
            return jsonify({"error": "No text provided"}), 400

        openai_key = os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            return jsonify({"error": "OpenAI API key not configured"}), 500

        import urllib.request
        import json as json_lib

        # alloy = neutral, warm, conversational English
        # shimmer = expressive, works well for Hindi/Marathi multilingual
        # nova = energetic/sweet, another good option
        voice = "shimmer" if language in ("hi", "mr") else "alloy"

        payload = json_lib.dumps({
            "model": "tts-1-hd",
            "input": text,
            "voice": voice,
            "speed": 0.95,          # Slightly slower -> more soothing, better for elderly
            "response_format": "mp3"
        }, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(
            "https://api.openai.com/v1/audio/speech",
            data=payload,
            headers={
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json",
            },
            method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            audio_bytes = resp.read()

        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return jsonify({"audio": audio_b64, "format": "mp3"})

    except Exception as e:
        logger.error(f"TTS error: {e}")
        return jsonify({"error": "TTS failed", "details": str(e)}), 500


@app.route("/api/vapi", methods=["POST"])
def vapi_custom_llm():
    """Custom LLM endpoint for Vapi. Follows OpenAI-like chat completion format."""
    try:
        data = request.get_json(force=True)
        # Vapi sends message history
        messages = data.get("messages", [])
        if not messages:
            return jsonify({"error": "No messages"}), 400
        
        last_user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        if not last_user_msg:
            return jsonify({"choices": [{"message": {"role": "assistant", "content": ""}}]})

        # Process through AVIRA brain
        result = assistant.process_input(last_user_msg)
        response = result.get("response", "")
        
        # Return in OpenAI format for Vapi
        return jsonify({
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": response
                    },
                    "finish_reason": "stop"
                }
            ]
        })
    except Exception as e:
        logger.error(f"Vapi LLM error: {e}")
        return jsonify({"choices": [{"message": {"role": "assistant", "content": "Sorry, I had a brain freeze."}}]}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "assistant": "AVIRA Phase 2 — ESP32 IoT (debug fixed)"})

@app.route("/api/frontend/events", methods=["GET"])
def get_frontend_events():
    """Return and clear pending events for the React frontend."""
    try:
        events = assistant.consume_frontend_events()
        return jsonify({"events": events})
    except Exception as e:
        logger.error(f"Frontend events error: {e}")
        return jsonify({"error": "Failed to fetch events"}), 500


# ── Entry point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  AVIRA — Elderly Care Voice Assistant API Server (DEBUG FIXED)")
    print("  Phase 2: ESP32 IoT Integration")
    print("=" * 60)
    print(f"  Backend:   http://localhost:5000")
    print(f"  Frontend:  http://localhost:5173")
    print(f"  Caregiver: http://localhost:5000/caregiver")
    print(f"  ESP32 IP:  {ESP32_IP}")
    print(f"  ESP32 URL: http://{ESP32_IP}/ping")
    print("=" * 60 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)

