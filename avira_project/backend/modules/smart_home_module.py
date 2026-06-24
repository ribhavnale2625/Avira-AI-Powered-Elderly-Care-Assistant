"""
Module 6: Smart Home Control — ESP32 IoT Integration (Phase 2)
Controls physical appliance states via HTTP REST calls to an ESP32 web server.
Falls back gracefully to in-memory simulation if ESP32 is unreachable.

Hardware:
  - LEDs (lights) controlled via PWM for brightness
  - DC motors (fans) controlled via PWM for speed
  - Relay (TV) for on/off
  - Servo (door lock) for lock/unlock
  - Buzzer + LED (offline SOS alert on ESP32)

Architecture:
  Flask backend  ──HTTP POST──►  ESP32 Web Server  ──GPIO──►  Physical devices
"""

import logging
import datetime
import json
import os

logger = logging.getLogger(__name__)


# ─── ESP32 Configuration ───────────────────────────────────────────────────
DEFAULT_ESP32_IP = os.environ.get("ESP32_IP", "192.168.1.100")


def _build_devices(esp32_ip: str) -> dict:
    """Build device definitions with the correct ESP32 IP."""
    base = f"http://{esp32_ip}"
    return {
        "light_living_room": {
            "id": "light_living_room",
            "name": "Living Room Light",
            "type": "light",
            "icon": "💡",
            "state": False,
            "brightness": 80,
            "color": "#FFF9C4",
            "room": "Living Room",
            "iot_endpoint": f"{base}/light/living",
        },
        "light_bedroom": {
            "id": "light_bedroom",
            "name": "Bedroom Light",
            "type": "light",
            "icon": "💡",
            "state": False,
            "brightness": 60,
            "color": "#E3F2FD",
            "room": "Bedroom",
            "iot_endpoint": f"{base}/light/bedroom",
        },
        "fan_living_room": {
            "id": "fan_living_room",
            "name": "Living Room Fan",
            "type": "fan",
            "icon": "🌀",
            "state": False,
            "speed": 3,
            "room": "Living Room",
            "iot_endpoint": f"{base}/fan/living",
        },
        "fan_bedroom": {
            "id": "fan_bedroom",
            "name": "Bedroom Fan",
            "type": "fan",
            "icon": "🌀",
            "state": False,
            "speed": 2,
            "room": "Bedroom",
            "iot_endpoint": f"{base}/fan/bedroom",
        },
        "tv": {
            "id": "tv",
            "name": "Television",
            "type": "tv",
            "icon": "📺",
            "state": False,
            "channel": 1,
            "volume": 30,
            "room": "Living Room",
            "iot_endpoint": f"{base}/tv",
        },
        "door_lock": {
            "id": "door_lock",
            "name": "Front Door Lock",
            "type": "lock",
            "icon": "🔒",
            "state": True,
            "room": "Entrance",
            "iot_endpoint": f"{base}/door",
        },
    }


class SmartHomeModule:
    """
    Smart home controller with ESP32 IoT integration.
    Sends HTTP commands to a real ESP32 web server for physical device control.
    Falls back to simulation mode if ESP32 is unreachable.
    """

    def __init__(self, use_iot: bool = False, esp32_ip: str = None,
                 state_file: str = None):
        self.use_iot = use_iot
        self.esp32_ip = esp32_ip or DEFAULT_ESP32_IP
        self.esp32_base_url = f"http://{self.esp32_ip}"
        self.esp32_connected = False
        self.fall_detection_ip = None
        self.state_file = state_file
        self.devices = {}
        self._change_log = []
        self._listeners = []

        self._load_devices()

        # Check ESP32 connectivity on startup if IoT mode is enabled
        if self.use_iot:
            self.esp32_connected = self.ping_esp32()
            if self.esp32_connected:
                logger.info(f"[OK] ESP32 connected at {self.esp32_ip}")
                self.sync_from_esp32()
            else:
                logger.warning(
                    f"[X] ESP32 unreachable at {self.esp32_ip} - "
                    f"running in simulation fallback mode"
                )

        logger.info(
            f"SmartHome initialized. Devices: {len(self.devices)}. "
            f"IoT: {self.use_iot}. ESP32: {self.esp32_ip}"
        )

    def _load_devices(self):
        """Load device states (from file if available, else defaults)."""
        if self.state_file and os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    saved = json.load(f)
                    self.devices = saved
                    # Update endpoints to current ESP32 IP
                    fresh = _build_devices(self.esp32_ip)
                    for dev_id in self.devices:
                        if dev_id in fresh:
                            self.devices[dev_id]["iot_endpoint"] = \
                                fresh[dev_id]["iot_endpoint"]
                    logger.info(f"Loaded {len(self.devices)} devices from {self.state_file}")
                    return
            except Exception as e:
                logger.warning(f"Could not load state file: {e}")

        self.devices = _build_devices(self.esp32_ip)

    def _save_devices(self):
        """Persist device states to file."""
        if self.state_file:
            try:
                with open(self.state_file, "w") as f:
                    json.dump(self.devices, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save device states: {e}")

    # ── ESP32 Connectivity ─────────────────────────────────────────────────

    def ping_esp32(self) -> bool:
        """Check if ESP32 is reachable, with rate limiting / caching to prevent blocking."""
        now = datetime.datetime.now()
        if hasattr(self, '_last_ping_time') and (now - self._last_ping_time).total_seconds() < 5:
            return self.esp32_connected
        
        self._last_ping_time = now
        try:
            import requests
            r = requests.get(f"{self.esp32_base_url}/ping", timeout=1.0)
            self.esp32_connected = r.status_code == 200
            return self.esp32_connected
        except Exception:
            self.esp32_connected = False
            return False

    def sync_from_esp32(self) -> dict:
        """
        Pull ESP32 status and verify connectivity.
        The simplified firmware returns {wifi, ip, sos} from /status.
        """
        try:
            import requests
            r = requests.get(f"{self.esp32_base_url}/status", timeout=1.0)
            if r.status_code != 200:
                return {"success": False, "message": "ESP32 returned non-200"}

            esp_data = r.json()
            self.esp32_connected = True
            logger.info(f"ESP32 sync OK - wifi={esp_data.get('wifi')}, ip={esp_data.get('ip')}")
            return {"success": True, "esp32_data": esp_data}

        except Exception as e:
            self.esp32_connected = False
            logger.warning(f"ESP32 sync failed: {e}")
            return {"success": False, "message": str(e)}

    def get_esp32_status(self) -> dict:
        """Return ESP32 connectivity info."""
        connected = self.ping_esp32() if self.use_iot else False
        return {
            "iot_enabled": self.use_iot,
            "esp32_ip": self.esp32_ip,
            "esp32_connected": connected,
            "esp32_url": self.esp32_base_url,
        }

    def update_esp32_ip(self, ip: str):
        """Update ESP32 IP dynamically and rebuild endpoints."""
        logger.info(f"Dynamically updating ESP32 IP from {self.esp32_ip} to {ip}")
        self.esp32_ip = ip
        self.esp32_base_url = f"http://{ip}"
        
        # Re-build/update the device endpoints to use the new IP
        fresh = _build_devices(self.esp32_ip)
        for dev_id in self.devices:
            if dev_id in fresh:
                self.devices[dev_id]["iot_endpoint"] = fresh[dev_id]["iot_endpoint"]
        
        # Ping check and synchronization
        self.esp32_connected = self.ping_esp32()
        if self.esp32_connected:
            logger.info(f"[OK] ESP32 connected at updated IP {self.esp32_ip}")
            self.sync_from_esp32()
        else:
            logger.warning(f"[X] ESP32 unreachable at updated IP {self.esp32_ip}")
        
        self._save_devices()

    # ── Device Control ─────────────────────────────────────────────────────

    def set_device(self, device_type: str, state: bool,
                   room: str = None, **kwargs) -> dict:
        """
        Set a device's on/off state. Forwards command to ESP32 if IoT is enabled.

        Args:
            device_type: 'light', 'fan', 'tv', 'lock'
            state: True = on/active, False = off/inactive
            room: Optional room filter ('living room', 'bedroom', etc.)
            **kwargs: Additional parameters (brightness, speed, etc.)

        Returns:
            Result dict with affected devices list
        """
        affected = []

        for device_id, device in self.devices.items():
            if device["type"] != device_type:
                continue
            if room:
                room_lower = room.lower().strip()
                if (room_lower not in device["room"].lower() and 
                    room_lower not in device["name"].lower() and 
                    room_lower not in device_id.lower()):
                    continue

            old_state = device["state"]
            device["state"] = state
            device["last_changed"] = datetime.datetime.now().isoformat()

            for key, value in kwargs.items():
                if key in device:
                    device[key] = value

            change = {
                "device_id": device_id,
                "device_name": device["name"],
                "old_state": old_state,
                "new_state": state,
                "timestamp": device["last_changed"],
                "extra_params": kwargs,
            }
            self._change_log.append(change)
            affected.append(device.copy())

            # Send command to ESP32 if IoT enabled
            if self.use_iot:
                self._send_iot_command(device, state, **kwargs)

            for callback in self._listeners:
                try:
                    callback(device_id, device.copy())
                except Exception as e:
                    logger.error(f"Listener callback error: {e}")

        if not affected:
            logger.warning(f"No devices found: type={device_type}, room={room}")

        self._save_devices()
        return {"success": bool(affected), "affected_devices": affected}

    def get_device_state(self, device_id: str) -> dict | None:
        """Get state of a specific device."""
        return self.devices.get(device_id)

    def get_all_devices(self) -> dict:
        """Return all device states."""
        return dict(self.devices)

    def get_devices_by_type(self, device_type: str) -> list:
        """Return all devices of a given type."""
        return [d for d in self.devices.values() if d["type"] == device_type]

    def set_device_by_id(self, device_id: str, state: bool = None, **kwargs) -> dict:
        """
        Set properties for a specific device by its unique ID.
        Forwards command to ESP32 if IoT is enabled.
        """
        device = self.devices.get(device_id)
        if not device:
            logger.warning(f"Device '{device_id}' not found.")
            return {"success": False, "message": f"Device {device_id} not found."}

        old_state = device["state"]
        if state is not None:
            device["state"] = state

        device["last_changed"] = datetime.datetime.now().isoformat()

        for key, value in kwargs.items():
            if key in device:
                device[key] = value

        change = {
            "device_id": device_id,
            "device_name": device["name"],
            "old_state": old_state,
            "new_state": device["state"],
            "timestamp": device["last_changed"],
            "extra_params": kwargs,
        }
        self._change_log.append(change)

        # Send command to ESP32 if IoT enabled
        if self.use_iot:
            self._send_iot_command(device, device["state"], **kwargs)

        for callback in self._listeners:
            try:
                callback(device_id, device.copy())
            except Exception as e:
                logger.error(f"Listener callback error: {e}")

        self._save_devices()
        return {"success": True, "affected_devices": [device.copy()]}

    def toggle_device(self, device_id: str) -> dict:
        """Toggle a specific device's on/off state."""
        device = self.devices.get(device_id)
        if not device:
            return {"success": False, "message": f"Device {device_id} not found."}

        new_state = not device["state"]
        return self.set_device_by_id(device_id, state=new_state)

    def get_home_summary(self) -> str:
        """Generate a human-readable home status summary."""
        on_devices = [d for d in self.devices.values() if d["state"]]
        off_devices = [d for d in self.devices.values() if not d["state"]]

        if not on_devices:
            return "All appliances are currently off."

        on_list = ", ".join(d["name"] for d in on_devices)
        return f"Currently on: {on_list}. {len(off_devices)} appliance(s) are off."

    def add_listener(self, callback):
        """Register a callback for device state changes."""
        self._listeners.append(callback)

    def remove_listener(self, callback):
        """Unregister a callback."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    # ── ESP32 IoT Commands ─────────────────────────────────────────────────

    def _send_iot_command(self, device: dict, state: bool, **kwargs):
        """
        Send command to physical ESP32 device via HTTP POST.
        Falls back silently to simulation if ESP32 is unreachable.
        Simplified payload: just {"state": true/false} for on/off control.
        """
        endpoint = device.get("iot_endpoint", "")
        if not endpoint:
            return

        payload = {"state": state}

        try:
            import requests
            response = requests.post(endpoint, json=payload, timeout=3)
            if response.status_code == 200:
                self.esp32_connected = True
                logger.info(
                    f"[OK] ESP32 command sent: {device['name']} -> "
                    f"{'ON' if state else 'OFF'}"
                )
            else:
                logger.warning(
                    f"ESP32 returned {response.status_code} for {device['name']}"
                )
        except Exception as e:
            self.esp32_connected = False
            logger.warning(
                f"[X] ESP32 unreachable for {device['name']}: {e} "
                f"(simulation fallback active)"
            )

    # ── Offline SOS (forwarded to ESP32) ───────────────────────────────────

    def trigger_sos_on_esp32(self) -> dict:
        """
        Trigger the offline SOS alert on ESP32.
        Activates buzzer + LED strobe + all lights flashing.
        Works even if the internet is down — only needs local WiFi.
        """
        try:
            import requests
            r = requests.post(
                f"{self.esp32_base_url}/sos/trigger",
                json={}, timeout=2
            )
            if r.status_code == 200:
                logger.critical("[SOS] ESP32 SOS alert ACTIVATED (offline capable)")
                return {"success": True, "message": "ESP32 SOS activated",
                        "offline_capable": True}
        except Exception as e:
            logger.error(f"Could not reach ESP32 for SOS: {e}")

        return {"success": False, "message": "ESP32 unreachable for SOS",
                "offline_capable": False}

    def cancel_sos_on_esp32(self) -> dict:
        """Cancel the offline SOS alert on ESP32."""
        try:
            import requests
            r = requests.post(
                f"{self.esp32_base_url}/sos/cancel",
                json={}, timeout=2
            )
            if r.status_code == 200:
                logger.info("ESP32 SOS alert cancelled")
                return {"success": True, "message": "ESP32 SOS cancelled"}
        except Exception as e:
            logger.error(f"Could not reach ESP32 to cancel SOS: {e}")

        return {"success": False, "message": "ESP32 unreachable"}

    # ── Status & Logs ──────────────────────────────────────────────────────

    def get_change_log(self, limit: int = 20) -> list:
        """Return recent device change log."""
        return self._change_log[-limit:]

    def get_status(self) -> dict:
        total = len(self.devices)
        on = len([d for d in self.devices.values() if d["state"]])
        return {
            "total_devices": total,
            "devices_on": on,
            "devices_off": total - on,
            "iot_enabled": self.use_iot,
            "esp32_ip": self.esp32_ip,
            "esp32_connected": self.esp32_connected,
            "change_log_entries": len(self._change_log),
        }
