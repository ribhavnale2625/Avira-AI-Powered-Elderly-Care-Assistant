<div align="center">

# 🤖 AVIRA
### AI-Powered Elderly Care Voice Assistant

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![ESP32](https://img.shields.io/badge/ESP32-IoT-E7352C?style=for-the-badge&logo=espressif&logoColor=white)](https://espressif.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

> **AVIRA** (*Adaptive Voice Intelligence for Real-time Assistance*) is a full-stack AI voice assistant designed specifically for elderly care — combining emotion-aware conversations, smart home IoT control, physics-based fall detection, and a remote caregiver portal into a single cohesive platform.

</div>

---

## 📋 Table of Contents

- [Problem Statement](#-problem-statement)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [API Reference](#-api-reference)
- [Hardware Setup (ESP32)](#-hardware-setup-esp32)
- [ML Models](#-ml-models)
- [Voice Commands](#-voice-commands)
- [Environment Variables](#-environment-variables)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Problem Statement

Over **700 million** elderly people worldwide live alone or with limited assistance. They face three critical daily challenges:

| Challenge | AVIRA's Solution |
|-----------|-----------------|
| Loneliness & mental health decline | Emotion-aware multilingual AI companion |
| Safety risks (falls, emergencies) | 5-state fall detection + multi-layer SOS |
| Difficulty operating smart devices | Natural voice-controlled smart home |

---

## ✨ Key Features

### 🗣️ Multilingual Voice Assistant
- **Languages**: English, Hindi (हिन्दी), Marathi (मराठी)
- Natural, warm, respectful conversational tone
- Voice input via Web Speech API; premium output via OpenAI TTS-1-HD
- LLM-powered natural conversations through Groq (LLaMA 3.1 8B Instant)
- Supports opening websites, searching Google, playing music on YouTube

### 🏠 Smart Home Automation (Voice + UI)
- Control lights, fans, TV, door lock, and buzzer via voice or touch
- Room-aware commands: *"Turn off the bedroom fan"*, *"Lock the door"*
- Real-time two-way state sync: **Frontend ↔ Backend ↔ ESP32 hardware**
- Real GPIO control via ESP32 (LEDs, relay modules, servo motor)

### 😊 Dual Emotion Detection
| Method | Technology | Output |
|--------|-----------|--------|
| **Text-based** | Custom BERT (HuggingFace Transformers + PyTorch) | 6 classes: joy, sadness, anger, fear, love, surprise |
| **Face-based** | FER-2013 CNN + MTCNN via webcam | 7 classes: angry, disgust, fear, happy, sad, surprise, neutral |

Emotion scores feed live **radar charts** and **mood trend analytics** in the UI.

### 🚨 Multi-Layer Emergency SOS
| Layer | Trigger | Mechanism |
|-------|---------|-----------|
| **Voice** | *"Help me"* / *"Emergency"* | Voice-activated SOS pipeline |
| **UI Button** | One-tap | Immediate SOS dispatch |
| **Fall Detection** | MPU6050 impact event | Automatic, always-on |
| **Hardware** | GPIO 22/23 | Offline buzzer + strobe — works without WiFi |

### 🤸 Physics-Based Fall Detection (5-State Machine)
```
MONITORING → FREE_FALL (<0.4g)
           → IMPACT (>2.5g within 1s)
           → VERIFYING (2s inactivity check)
           → WARNING (5s buzzer + LED, cancel button available)
           → ALERTING (SOS to backend + home ESP32)
           → COOLOFF (10s anti-duplicate window)
```
- Boot-time calibration: 200 samples for offset correction
- Physical cancel button (GPIO 12) for false alarm override
- Cross-ESP32 communication via WiFi HTTP

### 👨‍⚕️ Caregiver Portal (Progressive Web App)
- **Real-time dashboard**: User info, last active time, current emotion, SOS status
- **Mood analytics**: Emotion history charts, alerts on 3+ consecutive negative emotions
- **Remote messaging**: Send messages that AVIRA speaks aloud immediately
- **Reminders**: Schedule one-time or daily timed reminders
- **Device monitoring**: View and manage all smart home states remotely
- **Conversation log**: Full transcript of all user interactions

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    AVIRA System Architecture                      │
├───────────────────┬──────────────────────┬───────────────────────┤
│   React Frontend  │    Python Backend     │   ESP32 Hardware      │
│   (Port 5173)     │    (Port 5000)        │   (WiFi HTTP)         │
│                   │                       │                       │
│  AssistantContext │  Flask REST API       │  ESP32 #1             │
│  ├─ Web Speech API│  ├─ Command Processor │  ├─ Lights (GPIO 2,4) │
│  ├─ SpeechSynth   │  │  └─ Groq LLaMA 3.1│  ├─ Fans (GPIO 5,18)  │
│  ├─ Emotion UI    │  ├─ Emotion Classifier│  ├─ TV (GPIO 19)      │
│  ├─ Smart Home UI │  │  └─ BERT PyTorch   │  ├─ Servo Lock (21)   │
│  ├─ SOS Button    │  ├─ Face Detector     │  └─ Buzzer+LED (22,23)│
│  └─ Caregiver PWA │  │  └─ FER CNN+MTCNN  │                       │
│                   │  ├─ TTS Module        │  ESP32 #2             │
│                   │  │  └─ OpenAI TTS-1-HD│  ├─ MPU6050 (I2C)    │
│                   │  ├─ Alert Module      │  ├─ 5-State Machine   │
│                   │  └─ Smart Home Module │  └─ Cancel Btn (12)   │
└───────────────────┴──────────────────────┴───────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | React + TypeScript + Vite | 19 / 5 / 6 | Main user interface |
| **UI Components** | shadcn/ui + Radix UI | Latest | Accessible component library |
| **Animations** | Motion (Framer) | 12 | Micro-animations, emotion orb |
| **Charts** | Recharts | 2 | Emotion analytics visualizations |
| **Styling** | Tailwind CSS | 4 | Utility-first styling |
| **Voice I/O** | Web Speech API | Browser-native | Zero-dependency voice input |
| **Premium TTS** | OpenAI TTS-1-HD | API | High-quality `alloy`/`shimmer` voices |
| **Backend** | Python Flask + Flask-CORS | 3.0 | REST API server |
| **AI / LLM** | Groq API → LLaMA 3.1 8B | Instant | NLU + JSON-structured intent parsing |
| **Emotion (Text)** | HuggingFace Transformers + PyTorch | BERT | 6-class emotion classification |
| **Emotion (Face)** | FER (FER-2013 CNN + MTCNN) | 22.5 | Webcam facial recognition |
| **Offline STT** | Vosk | 0.3.32 | On-device speech recognition |
| **IoT** | ESP32 + Arduino IDE | — | Real hardware GPIO control |
| **Fall Detection** | MPU6050 gyro/accelerometer | I2C | Physics-based fall algorithm |

---

## 📁 Project Structure

```
AVIRA_Full_Project/
├── .gitignore                        ← Protects secrets & build artifacts
│
├── avira_project/
│   │
│   ├── frontend/                     ← React + TypeScript PWA
│   │   ├── index.html
│   │   ├── vite.config.ts
│   │   ├── package.json
│   │   └── src/
│   │       ├── main.tsx              ← App entry point
│   │       ├── app/
│   │       │   ├── App.tsx           ← Root layout + routing
│   │       │   ├── context/
│   │       │   │   └── AssistantContext.tsx  ← Central state + all logic
│   │       │   └── components/
│   │       │       ├── Header.tsx            ← AVIRA logo, live clock, mic
│   │       │       ├── AIOrb.tsx             ← Emotion-reactive animated orb
│   │       │       ├── ConversationPanel.tsx ← Live chat + voice input
│   │       │       ├── SmartHomeControl.tsx  ← Room-grouped device controls
│   │       │       ├── EmotionAnalytics.tsx  ← Live emotion bars + charts
│   │       │       ├── MoodInsight.tsx       ← Mood pattern analysis
│   │       │       ├── SystemStatus.tsx      ← Module health indicators
│   │       │       ├── ActivityLog.tsx       ← Live event feed
│   │       │       ├── EmergencySOS.tsx      ← SOS button + contacts
│   │       │       └── QuickCommands.tsx     ← One-tap command chips
│   │       └── styles/
│   │
│   ├── backend/                      ← Python Flask REST API
│   │   ├── server.py                 ← Main API server (28+ endpoints)
│   │   ├── assistant.py              ← Core orchestrator
│   │   ├── caregiver_routes.py       ← Caregiver portal Blueprint
│   │   ├── requirements.txt          ← Python dependencies
│   │   ├── .env.example              ← Environment variable template ⚠️
│   │   ├── modules/
│   │   │   ├── command_processor.py        ← Intent routing + Groq LLM
│   │   │   ├── emotion_classifier.py       ← BERT text emotion model
│   │   │   ├── face_emotion_module.py      ← FER-2013 face detection
│   │   │   ├── smart_home_module.py        ← ESP32 device controller
│   │   │   ├── alert_module.py             ← SOS + notification system
│   │   │   ├── speech_recognition_module.py← Vosk offline STT
│   │   │   └── tts_module.py               ← OpenAI / pyttsx3 / gTTS
│   │   ├── models/
│   │   │   ├── emotion_model/              ← BERT model weights
│   │   │   ├── vosk-model-small-en-us-0.15/← English offline STT
│   │   │   └── vosk-model-small-hi-0.22/   ← Hindi offline STT
│   │   └── caregiver/                      ← Caregiver PWA static files
│   │       ├── index.html
│   │       ├── manifest.json
│   │       └── sw.js
│   │
│   └── esp32/                        ← Arduino / ESP32 firmware
│       ├── esp32_firmware.ino        ← Home automation (lights, fans, servo)
│       ├── esp32_gyro_firmware.ino   ← Fall detection (MPU6050, 5-state FSM)
│       └── README_ESP32.md           ← Wiring diagrams + flashing guide
│
└── ml_models/                         ← Pre-trained ML model artifacts
    ├── emotion_model.h5              ← Keras model (13.5 MB)
    ├── emotion_scaler.pkl            ← Scikit-learn StandardScaler
    └── label_encoder.pkl             ← Label encoder (6 emotion classes)
```

---

## 🚀 Getting Started

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.10+ | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| Git | Latest | [git-scm.com](https://git-scm.com) |
| Chrome / Edge | Latest | Required for Web Speech API |

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/AVIRA.git
cd AVIRA
```

### 2. Configure Environment Variables

```bash
cd avira_project/backend
cp .env.example .env
# Open .env and fill in your actual API keys (see Environment Variables section)
```

### 3A. Frontend Only (No Python Required)

The React frontend is fully self-contained — all core logic runs in TypeScript.

```bash
cd avira_project/frontend
npm install
npm run dev
# Open http://localhost:5173 in Chrome or Edge
```

> ⚠️ **Use Chrome or Edge** — Safari does not support the Web Speech API.

### 3B. Full Stack (Frontend + Python Backend)

**Terminal 1 — Backend**
```bash
cd avira_project/backend
pip install -r requirements.txt
python server.py
# API running at http://localhost:5000
```

**Terminal 2 — Frontend**
```bash
cd avira_project/frontend
npm install
npm run dev
# App running at http://localhost:5173
```

---

## 📡 API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/process` | Process a voice/text command through the full AI pipeline |
| `GET` | `/api/status` | Full system status (all modules + ESP32 connectivity) |
| `GET` | `/api/history` | Conversation history |
| `GET` | `/api/languages` | Supported languages |
| `POST` | `/api/set-language` | Change active language |

### Smart Home

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/devices` | Get all smart home device states |
| `POST` | `/api/devices/<id>/toggle` | Toggle a device |
| `POST` | `/api/devices/<id>/set` | Set device properties |
| `GET` | `/api/home/summary` | Human-readable home status |
| `GET` | `/api/esp32/status` | ESP32 connectivity check |
| `POST` | `/api/esp32/sync` | Sync device states from ESP32 |

### Emergency / SOS

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/sos/trigger` | Trigger emergency SOS |
| `POST` | `/api/sos/cancel` | Cancel active SOS |

### AI / Media

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/face-emotion` | Detect emotion from base64 webcam frame |
| `POST` | `/api/tts` | Text-to-speech via OpenAI TTS-1-HD |
| `POST` | `/api/vapi` | Custom LLM endpoint for Vapi voice calls |

### Caregiver Portal

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/caregiver/dashboard` | Full caregiver dashboard data |
| `GET` | `/api/caregiver/mood-history` | Emotion prediction history |
| `GET` | `/api/caregiver/conversations` | Full conversation log |
| `GET` | `/api/caregiver/alerts` | SOS alert history |
| `GET` | `/api/caregiver/devices` | Remote device states |
| `POST` | `/api/caregiver/send-message` | Push message to AVIRA (spoken aloud) |
| `POST` | `/api/caregiver/set-reminder` | Schedule a one-time or daily reminder |
| `GET` | `/api/caregiver/reminders` | List all active reminders |
| `DELETE` | `/api/caregiver/delete-reminder` | Cancel a reminder |

---

## 🔌 Hardware Setup (ESP32)

### ESP32 #1 — Home Automation

| Device | GPIO | Component |
|--------|------|-----------|
| Living Room Light | 2 | LED + 220Ω resistor |
| Bedroom Light | 4 | LED + 220Ω resistor |
| Living Room Fan | 5 | Motor module / LED indicator |
| Bedroom Fan | 18 | Motor module / LED indicator |
| Television | 19 | Relay module |
| Door Lock | 21 | SG90 Servo motor |
| SOS Buzzer | 22 | Active buzzer |
| SOS LED | 23 | Red LED + 220Ω resistor |

### ESP32 #2 — Fall Detection

| Function | GPIO | Component |
|----------|------|-----------|
| Warning Buzzer | 14 | Active buzzer |
| Status LED | 13 | LED indicator |
| Cancel Button | 12 | Push-button (INPUT_PULLUP) |
| MPU6050 SDA | 21 | I2C data line |
| MPU6050 SCL | 22 | I2C clock line |

### Flashing Firmware

```bash
# 1. Install Arduino IDE with ESP32 board support
# 2. Install required libraries: MPU6050, ArduinoJSON, WebServer

# Flash ESP32 #1 (Home Automation)
# Open: avira_project/esp32/esp32_firmware.ino
# Set WiFi SSID/Password and upload

# Flash ESP32 #2 (Fall Detection)
# Open: avira_project/esp32/esp32_gyro_firmware.ino
# Set WiFi SSID/Password and upload

# Set ESP32 IP in your .env
ESP32_IP=192.168.x.x   # Replace with your ESP32's actual IP
```

---

## 🧠 ML Models

| Model | Architecture | Size | Purpose |
|-------|-------------|------|---------|
| **Text Emotion** | BERT (`AutoModelForSequenceClassification`) | ~420 MB | Classify text into 6 emotion classes; negation-aware |
| **Face Emotion** | FER-2013 CNN + MTCNN | Bundled | Webcam facial expression → 7 emotion labels |
| **Emotion v2** | Keras `.h5` + scikit-learn | 13.5 MB | Saved model artifacts in `ml_models/` |
| **LLM** | LLaMA 3.1 8B Instant (Groq Cloud) | Cloud API | Natural conversation + JSON intent extraction |
| **Offline STT** | Vosk (small EN + HI models) | ~50 MB each | On-device speech recognition, no internet needed |

> 💡 **Model downloads**: Run `backend/models/download_vosk_models.py` to fetch Vosk models automatically.

---

## 🎤 Voice Commands

| Category | Say… | Action |
|----------|------|--------|
| **Smart Home** | *"Turn on the lights"* | All lights on (ESP32 GPIO) |
| **Smart Home** | *"Turn off the bedroom fan"* | Bedroom fan off only |
| **Smart Home** | *"Lock the door"* | Servo motor locks door |
| **Smart Home** | *"Turn on the TV"* | Relay activates TV |
| **Time / Info** | *"What time is it?"* | Speaks current time |
| **Time / Info** | *"Today's date"* | Speaks current date |
| **Media** | *"Play relaxing music"* | Opens YouTube – calming playlist |
| **Media** | *"Play Hindi music"* | Opens YouTube – Hindi songs |
| **Web** | *"Open Netflix"* | Opens Netflix in browser |
| **Web** | *"Search for diabetes diet"* | Google search |
| **Chitchat** | *"Tell me a joke"* | Responds with a random joke |
| **Emotional** | *"I'm feeling lonely"* | Emotional support + sadness logged |
| **Emergency** | *"Help me!"* / *"Emergency"* | 🚨 Full SOS pipeline triggered |

---

## 🔐 Environment Variables

Copy `.env.example` to `.env` inside `avira_project/backend/` and set:

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | [Groq Console](https://console.groq.com) — LLaMA 3.1 access |
| `OPENAI_API_KEY` | Yes | [OpenAI Platform](https://platform.openai.com) — TTS-1-HD |
| `ESP32_IP` | No | Local IP of your ESP32 board (e.g. `192.168.1.42`) |

> ⚠️ **Security**: The `.env` file is listed in `.gitignore` and will **never** be pushed to GitHub. Only `.env.example` (with placeholder values) is committed.

---

## 📊 Project Metrics

| Metric | Value |
|--------|-------|
| Backend API endpoints | **28+** |
| Frontend React components | **10** |
| Python backend modules | **7** |
| ESP32 firmware files | **2** |
| Supported languages | **3** (EN, HI, MR) |
| Text emotion classes | **6** (joy, sadness, anger, fear, love, surprise) |
| Face emotion classes | **7** (angry, disgust, fear, happy, sad, surprise, neutral) |
| Smart home device types | **5** (light, fan, TV, lock, buzzer) |
| Fall detection states | **5** (monitoring, verifying, warning, alerting, cooloff) |
| ML models integrated | **3** (BERT, FER-CNN, LLaMA 3.1) |
| Caregiver portal endpoints | **9** |

---

## 🔮 Roadmap

- [x] **Phase 1** — Full-stack prototype (React + Python + ESP32)
- [x] **Phase 1** — Dual emotion detection (text + face)
- [x] **Phase 1** — Caregiver PWA portal
- [x] **Phase 1** — ESP32 fall detection (5-state machine)
- [ ] **Phase 2** — Real SMS alerts via Twilio integration
- [ ] **Phase 2** — Wake word detection (Picovoice Porcupine)
- [ ] **Phase 3** — OpenCV video-based fall detection (camera alternative)
- [ ] **Phase 3** — BLE health sensor integration (heart rate, SpO₂)
- [ ] **Phase 3** — Mobile companion app (React Native)

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a Pull Request

Please ensure your code follows the existing style and includes relevant comments.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Ribhav Nale**  
Engineering Student | AI/ML & Full-Stack Developer  
📧 [ribhavnale2625@gmail.com](mailto:ribhavnale2625@gmail.com) | 🔗 [GitHub](https://github.com/ribhavnale2625)

---

<div align="center">

**Built with ❤️ for elderly care — because technology should serve humanity.**

⭐ If this project helped you, please give it a star!

</div>
