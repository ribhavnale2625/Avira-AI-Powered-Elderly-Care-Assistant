"""
AVIRA Caregiver Portal — Flask Blueprint
API endpoints for the caregiver PWA to monitor and interact with the elderly user.
"""

import os
import logging
from flask import Blueprint, request, jsonify, send_from_directory

logger = logging.getLogger("AVIRA-Caregiver")

# Create Blueprint
caregiver_bp = Blueprint('caregiver', __name__)

# Reference to assistant (set during registration)
_assistant = None


def init_caregiver(assistant):
    """Called from server.py to inject the assistant reference."""
    global _assistant
    _assistant = assistant


# ── Serve PWA ────────────────────────────────────────────────────────────────

CAREGIVER_DIR = os.path.join(os.path.dirname(__file__), "caregiver")


@caregiver_bp.route("/caregiver")
@caregiver_bp.route("/caregiver/")
def serve_caregiver():
    """Serve the caregiver PWA."""
    return send_from_directory(CAREGIVER_DIR, "index.html")


@caregiver_bp.route("/caregiver/<path:filename>")
def serve_caregiver_static(filename):
    """Serve PWA static assets (manifest, sw, icons)."""
    return send_from_directory(CAREGIVER_DIR, filename)


# ── Dashboard ────────────────────────────────────────────────────────────────

@caregiver_bp.route("/api/caregiver/dashboard", methods=["GET"])
def dashboard():
    """Return full dashboard data for the caregiver."""
    try:
        return jsonify(_assistant.get_caregiver_dashboard())
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return jsonify({"error": str(e)}), 500


# ── Mood History ─────────────────────────────────────────────────────────────

@caregiver_bp.route("/api/caregiver/mood-history", methods=["GET"])
def mood_history():
    """Return emotion prediction history."""
    try:
        return jsonify(_assistant.get_emotion_history())
    except Exception as e:
        logger.error(f"Mood history error: {e}")
        return jsonify({"error": str(e)}), 500


# ── Conversations ────────────────────────────────────────────────────────────

@caregiver_bp.route("/api/caregiver/conversations", methods=["GET"])
def conversations():
    """Return conversation history."""
    try:
        limit = int(request.args.get("limit", 50))
        return jsonify(_assistant.get_conversation_history(limit))
    except Exception as e:
        logger.error(f"Conversations error: {e}")
        return jsonify({"error": str(e)}), 500


# ── SOS Alerts ───────────────────────────────────────────────────────────────

@caregiver_bp.route("/api/caregiver/alerts", methods=["GET"])
def alerts():
    """Return SOS alert history."""
    try:
        return jsonify({
            "active": _assistant.alerts._active,
            "history": _assistant.alerts.get_alert_history(),
        })
    except Exception as e:
        logger.error(f"Alerts error: {e}")
        return jsonify({"error": str(e)}), 500


# ── Devices ──────────────────────────────────────────────────────────────────

@caregiver_bp.route("/api/caregiver/devices", methods=["GET"])
def devices():
    """Return smart home device states."""
    try:
        return jsonify(_assistant.smart_home.get_all_devices())
    except Exception as e:
        logger.error(f"Devices error: {e}")
        return jsonify({"error": str(e)}), 500


# ── Send Message ─────────────────────────────────────────────────────────────

@caregiver_bp.route("/api/caregiver/send-message", methods=["POST"])
def send_message():
    """Send a message to the elderly user. AVIRA speaks it aloud."""
    try:
        data = request.get_json(force=True)
        text = data.get("text", "").strip()
        from_name = data.get("from", "Caregiver")
        if not text:
            return jsonify({"error": "No message text provided"}), 400
        result = _assistant.queue_caregiver_message(text, from_name)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Send message error: {e}")
        return jsonify({"error": str(e)}), 500


@caregiver_bp.route("/api/caregiver/sent-messages", methods=["GET"])
def sent_messages():
    """Return log of all messages sent by caregiver."""
    try:
        return jsonify(_assistant.get_caregiver_sent_log())
    except Exception as e:
        logger.error(f"Sent messages error: {e}")
        return jsonify({"error": str(e)}), 500


# ── Reminders ────────────────────────────────────────────────────────────────

@caregiver_bp.route("/api/caregiver/set-reminder", methods=["POST"])
def set_reminder():
    """Set a timed reminder for the elderly user."""
    try:
        data = request.get_json(force=True)
        text = data.get("text", "").strip()
        time_str = data.get("time", "").strip()
        repeat = data.get("repeat", "once")
        if not text or not time_str:
            return jsonify({"error": "Both 'text' and 'time' are required"}), 400
        result = _assistant.add_reminder(text, time_str, repeat)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Set reminder error: {e}")
        return jsonify({"error": str(e)}), 500


@caregiver_bp.route("/api/caregiver/reminders", methods=["GET"])
def reminders():
    """Return all reminders."""
    try:
        return jsonify(_assistant.get_reminders())
    except Exception as e:
        logger.error(f"Reminders error: {e}")
        return jsonify({"error": str(e)}), 500


@caregiver_bp.route("/api/caregiver/delete-reminder", methods=["DELETE"])
def delete_reminder():
    """Cancel a reminder by ID."""
    try:
        data = request.get_json(force=True)
        reminder_id = data.get("id", "")
        if not reminder_id:
            return jsonify({"error": "Reminder 'id' required"}), 400
        result = _assistant.cancel_reminder(reminder_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Delete reminder error: {e}")
        return jsonify({"error": str(e)}), 500
