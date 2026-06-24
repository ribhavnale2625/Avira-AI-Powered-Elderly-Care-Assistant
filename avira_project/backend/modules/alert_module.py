"""
Module 5: Emergency SOS Alert System
Handles emergency detection and alert dispatch.
Supports email simulation, SMS simulation, and local logging.
"""

import logging
import datetime
import json
import os
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class EmergencyAlertModule:
    """
    Emergency SOS alert system for elderly care.
    
    Phase 1: Simulates alert dispatch with logging + optional email.
    Future: SMS via Twilio, IoT panic button integration, caregiver app push notifications.
    """

    def __init__(self, user_name: str = "User", caregiver_contacts: list = None,
                 email_config: dict = None, log_dir: str = "logs"):
        self.user_name = user_name
        self.caregiver_contacts = caregiver_contacts or [
            {"name": "Primary Caregiver", "phone": "+91-XXXXXXXXXX",
             "email": "caregiver@example.com", "relation": "Caregiver"}
        ]
        self.email_config = email_config or {}
        self.log_dir = log_dir
        self.alert_count = 0
        self.alert_history = []
        self._active = False

        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)

    def trigger_sos(self, trigger_type: str = "voice",
                    location: str = "Home", additional_info: str = "") -> dict:
        """
        Trigger an emergency SOS alert.
        
        Args:
            trigger_type: 'voice', 'button', or 'sensor'
            location: Where the alert was triggered
            additional_info: Any additional context
            
        Returns:
            Alert result dictionary
        """
        if self._active:
            logger.warning("SOS already active, skipping duplicate trigger.")
            return {"success": False, "message": "SOS already active."}

        self._active = True
        self.alert_count += 1

        timestamp = datetime.datetime.now()
        alert_id = f"SOS-{timestamp.strftime('%Y%m%d-%H%M%S')}-{self.alert_count:03d}"

        alert_data = {
            "alert_id": alert_id,
            "timestamp": timestamp.isoformat(),
            "user_name": self.user_name,
            "trigger_type": trigger_type,
            "location": location,
            "additional_info": additional_info,
            "contacts_notified": [],
            "status": "triggered",
        }

        logger.critical(f"🚨 SOS ALERT TRIGGERED: {alert_id}")
        logger.critical(f"User: {self.user_name} | Trigger: {trigger_type} | Location: {location}")

        # Dispatch alerts in background thread
        dispatch_thread = threading.Thread(
            target=self._dispatch_all_alerts,
            args=(alert_data,),
            daemon=True
        )
        dispatch_thread.start()

        # Log to file immediately
        self._log_alert(alert_data)
        self.alert_history.append(alert_data)

        return {
            "success": True,
            "alert_id": alert_id,
            "message": f"Emergency SOS alert {alert_id} has been triggered. "
                       f"Notifying {len(self.caregiver_contacts)} contact(s). "
                       f"Help is on the way!",
            "timestamp": timestamp.strftime("%I:%M:%S %p on %B %d, %Y"),
            "contacts": [c["name"] for c in self.caregiver_contacts],
        }

    def _dispatch_all_alerts(self, alert_data: dict):
        """Dispatch alerts to all configured channels."""
        for contact in self.caregiver_contacts:
            # Simulate SMS
            sms_result = self._send_sms_simulation(contact, alert_data)
            # Attempt real email if configured
            email_result = self._send_email(contact, alert_data)

            contact_result = {
                "contact": contact["name"],
                "phone": contact.get("phone", "N/A"),
                "email": contact.get("email", "N/A"),
                "sms_sent": sms_result,
                "email_sent": email_result,
            }
            alert_data["contacts_notified"].append(contact_result)

        alert_data["status"] = "dispatched"
        self._log_alert(alert_data)
        self._active = False
        logger.info(f"SOS alert {alert_data['alert_id']} fully dispatched.")

    def _send_sms_simulation(self, contact: dict, alert_data: dict) -> bool:
        """
        Simulate SMS sending.
        
        Future: Replace with Twilio/AWS SNS for real SMS dispatch.
        """
        message = self._compose_alert_message(contact, alert_data, format="sms")
        logger.info(f"[SIMULATED SMS] → {contact['name']} ({contact.get('phone', 'N/A')})")
        logger.info(f"Message: {message}")

        # Save to simulation log
        sim_log_path = os.path.join(self.log_dir, "simulated_sms.log")
        with open(sim_log_path, "a") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"SIMULATED SMS - {datetime.datetime.now().isoformat()}\n")
            f.write(f"TO: {contact['name']} - {contact.get('phone', 'N/A')}\n")
            f.write(f"MESSAGE:\n{message}\n")

        return True  # Simulated success

    def _send_email(self, contact: dict, alert_data: dict) -> bool:
        """
        Send email alert to caregiver.
        Requires email_config with: sender, password, smtp_server, smtp_port.
        """
        if not self.email_config.get("sender"):
            logger.info("Email not configured, skipping email dispatch.")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🚨 EMERGENCY ALERT - {self.user_name} needs help!"
            msg["From"] = self.email_config["sender"]
            msg["To"] = contact.get("email", "")

            if not msg["To"]:
                return False

            text_body = self._compose_alert_message(contact, alert_data, format="email")
            html_body = self._compose_html_email(contact, alert_data)

            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            server = smtplib.SMTP_SSL(
                self.email_config.get("smtp_server", "smtp.gmail.com"),
                self.email_config.get("smtp_port", 465)
            )
            server.login(self.email_config["sender"], self.email_config["password"])
            server.sendmail(self.email_config["sender"], contact["email"], msg.as_string())
            server.quit()

            logger.info(f"Email sent to {contact['name']} <{contact['email']}>")
            return True

        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False

    def _compose_alert_message(self, contact: dict, alert_data: dict,
                                format: str = "sms") -> str:
        """Compose alert message text."""
        ts = datetime.datetime.fromisoformat(alert_data["timestamp"])
        time_str = ts.strftime("%I:%M %p on %B %d, %Y")

        if format == "sms":
            return (
                f"🚨 EMERGENCY ALERT\n"
                f"Dear {contact['name']},\n"
                f"{self.user_name} has triggered an emergency SOS alert!\n"
                f"Trigger: {alert_data['trigger_type'].upper()}\n"
                f"Location: {alert_data['location']}\n"
                f"Time: {time_str}\n"
                f"Alert ID: {alert_data['alert_id']}\n"
                f"Please check on them IMMEDIATELY.\n"
                f"— Elderly Care Assistant"
            )
        else:
            return (
                f"Dear {contact['name']},\n\n"
                f"This is an automated emergency alert from the Elderly Care Assistant.\n\n"
                f"{self.user_name} has triggered an emergency SOS alert.\n\n"
                f"Details:\n"
                f"• Trigger Type: {alert_data['trigger_type'].upper()}\n"
                f"• Location: {alert_data['location']}\n"
                f"• Time: {time_str}\n"
                f"• Alert ID: {alert_data['alert_id']}\n\n"
                f"Please check on {self.user_name} IMMEDIATELY.\n\n"
                f"This message was sent by the Elderly Care Voice Assistant System.\n"
            )

    def _compose_html_email(self, contact: dict, alert_data: dict) -> str:
        """Compose HTML email for visual alert."""
        ts = datetime.datetime.fromisoformat(alert_data["timestamp"])
        time_str = ts.strftime("%I:%M %p on %B %d, %Y")

        return f"""
        <html><body style="font-family: Arial; background: #fff0f0; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background: white; border-radius: 10px;
                    border-left: 8px solid #d32f2f; padding: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h1 style="color: #d32f2f;">🚨 EMERGENCY ALERT</h1>
            <p style="font-size: 18px;">Dear <strong>{contact['name']}</strong>,</p>
            <p style="font-size: 16px; background: #ffebee; padding: 15px; border-radius: 8px;">
                <strong>{self.user_name}</strong> has triggered an emergency SOS alert and needs help!
            </p>
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <tr><td style="padding: 8px; color: #666;">Trigger Type</td>
                    <td style="padding: 8px; font-weight: bold;">{alert_data['trigger_type'].upper()}</td></tr>
                <tr style="background: #f5f5f5;"><td style="padding: 8px; color: #666;">Location</td>
                    <td style="padding: 8px; font-weight: bold;">{alert_data['location']}</td></tr>
                <tr><td style="padding: 8px; color: #666;">Time</td>
                    <td style="padding: 8px; font-weight: bold;">{time_str}</td></tr>
                <tr style="background: #f5f5f5;"><td style="padding: 8px; color: #666;">Alert ID</td>
                    <td style="padding: 8px; font-weight: bold;">{alert_data['alert_id']}</td></tr>
            </table>
            <p style="margin-top: 20px; font-size: 16px; color: #d32f2f; font-weight: bold;">
                Please check on {self.user_name} IMMEDIATELY.
            </p>
            <hr style="margin-top: 30px; border: none; border-top: 1px solid #eee;">
            <p style="font-size: 12px; color: #999;">
                Sent by Elderly Care Voice Assistant System | Phase-1 Prototype
            </p>
        </div>
        </body></html>
        """

    def _log_alert(self, alert_data: dict):
        """Save alert to JSON log file."""
        log_path = os.path.join(self.log_dir, "emergency_alerts.json")
        alerts = []

        if os.path.exists(log_path):
            try:
                with open(log_path, "r") as f:
                    alerts = json.load(f)
            except Exception:
                alerts = []

        alerts.append(alert_data)

        with open(log_path, "w") as f:
            json.dump(alerts, f, indent=2)

    def cancel_alert(self, alert_id: str = None):
        """Cancel/resolve an active alert."""
        self._active = False
        logger.info(f"Alert {alert_id or 'current'} cancelled/resolved.")
        return {"success": True, "message": "Alert has been cancelled."}

    def get_alert_history(self) -> list:
        """Return alert history."""
        return self.alert_history

    def get_status(self) -> dict:
        return {
            "active_alert": self._active,
            "total_alerts": self.alert_count,
            "email_configured": bool(self.email_config.get("sender")),
            "contacts_count": len(self.caregiver_contacts),
        }
