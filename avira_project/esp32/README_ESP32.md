# AVIRA — ESP32 IoT Hardware Setup

## Required Hardware
- ESP32 Dev Board (any variant)
- LEDs × 2 + 220Ω resistors (lights)
- DC Motor or extra LEDs × 2 (fans)
- Relay module (TV)
- Servo motor SG90 (door lock)
- Active buzzer (SOS alert)
- Red LED + 220Ω resistor (SOS indicator)
- Breadboard + jumper wires

## Wiring

| Function           | GPIO | Component         |
|--------------------|------|-------------------|
| Living Room Light  | 2    | LED + 220Ω        |
| Bedroom Light      | 4    | LED + 220Ω        |
| Living Room Fan    | 5    | Motor / LED       |
| Bedroom Fan        | 18   | Motor / LED       |
| TV                 | 19   | Relay IN          |
| Door Lock          | 21   | Servo signal      |
| SOS Buzzer         | 22   | Active buzzer +   |
| SOS LED            | 23   | Red LED + 220Ω    |

> **Tip:** For a quick demo, use LEDs on all pins. Replace with relays/motors later.

## Arduino IDE Setup

1. **Install ESP32 board support:**
   - File → Preferences → Additional Board URLs:
     `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   - Tools → Board → Board Manager → search "esp32" → Install

2. **Install libraries** (Sketch → Include Library → Manage Libraries):
   - `ArduinoJson` (by Benoit Blanchon, v7+)
   - `ESP32Servo` (by Kevin Harrington)

3. **Edit `esp32_firmware.ino`:**
   - Set your WiFi SSID and password (lines 36–37)

4. **Upload:**
   - Select board: `ESP32 Dev Module`
   - Select port (COM port of your ESP32)
   - Click Upload

5. **Get your ESP32 IP:**
   - Open Serial Monitor (115200 baud)
   - Look for: `IP Address: 192.168.x.x`
   - Use this IP in the AVIRA backend config

## Backend Configuration

Set the ESP32 IP before starting the server:

```bash
# Windows PowerShell
$env:ESP32_IP = "192.168.1.100"
python server.py

# Linux / Mac
ESP32_IP=192.168.1.100 python server.py
```

## Offline SOS

The emergency system works **without WiFi or internet**:
- When SOS is triggered, GPIO 22 (buzzer) and GPIO 23 (LED) flash at 5Hz
- All house lights (GPIO 2, 4) also strobe at full brightness
- Auto-cancels after 5 minutes
- Can be triggered via the web UI (if connected) or directly via `/sos/trigger`

## Quick Test

After flashing and connecting to WiFi:

```bash
# Health check
curl http://192.168.1.100/ping

# Turn on living room light
curl -X POST http://192.168.1.100/light/living -d '{"state":true,"brightness":200}'

# Get all device states
curl http://192.168.1.100/status

# Trigger SOS
curl -X POST http://192.168.1.100/sos/trigger
```
