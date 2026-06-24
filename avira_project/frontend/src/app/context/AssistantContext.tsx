/**
 * AVIRA – Elderly Care Voice Assistant
 * Central React Context — mirrors all 6 Python backend modules:
 *   Module 1: SpeechRecognitionModule  → toggleListening / Web Speech API
 *   Module 2: TextToSpeechModule       → speak() / Web Speech Synthesis
 *   Module 3: CommandProcessor         → processCommand()
 *   Module 4: EmotionDetectionModule   → detectEmotion()
 *   Module 5: EmergencyAlertModule     → triggerSOS() / cancelSOS()
 *   Module 6: SmartHomeModule          → device state + dispatch actions
 */

import React, {
  createContext, useContext, useReducer, useRef,
  useCallback, useEffect, useState,
} from 'react'

import axios from 'axios'
import Vapi from '@vapi-ai/web'
import { LANGUAGES, UI_STRINGS, type LangCode, DEFAULT_LANG } from '../config/languages'
const API_URL = window.location.protocol + '//' + window.location.hostname + ':5000'

// ─── Types ────────────────────────────────────────────────────────────────────
export type EmotionType = 'neutral' | 'joy' | 'sadness' | 'fear' | 'anger' | 'love' | 'surprise'
export type DeviceType  = 'light' | 'fan' | 'tv' | 'lock' | 'sensor'
export type LogType     = 'command' | 'device' | 'sos' | 'system'

export interface Message {
  id: string
  text: string
  sender: 'user' | 'ai'
  timestamp: Date
  emotion?: EmotionType
}

export interface ActivityEntry {
  id: string
  text: string
  type: LogType
  timestamp: Date
}

export interface Device {
  id: string
  name: string
  type: DeviceType
  iconName: string
  room: string
  state: boolean
  brightness?: number   // lights  0–100
  speed?: number        // fans    1–5
  volume?: number       // tv      0–100
  value?: string        // sensors display value
  lastToggled?: number  // timestamp of last user toggle/slider interaction
}

export interface EmotionScores {
  happy: number
  calm: number
  sad: number
  anxious: number
}

export interface AssistantState {
  isListening: boolean
  isSpeaking: boolean
  currentEmotion: EmotionType
  emotionScores: EmotionScores
  emotionHistory: Array<{ time: string; happy: number; calm: number; sad: number; anxious: number }>
  faceEmotion: string | null
  faceConfidence: number
  cameraActive: boolean
  sosActive: boolean
  sosAlertId: string | null
  messages: Message[]
  activityLog: ActivityEntry[]
  devices: Record<string, Device>
  stats: { conversations: number; alertsToday: number; healthScore: number; devicesOn: number }
  userName: string
  systemStatus: Record<string, { label: string; status: string; color: string }>
  activePage: 'dashboard' | 'analytics'
  currentLanguage: LangCode
}

// ─── Actions ──────────────────────────────────────────────────────────────────
type Action =
  | { type: 'SET_LISTENING';    payload: boolean }
  | { type: 'SET_SPEAKING';     payload: boolean }
  | { type: 'SET_EMOTION';      payload: { emotion: EmotionType; scores: EmotionScores } }
  | { type: 'ADD_MESSAGE';      payload: Message }
  | { type: 'ADD_LOG';          payload: ActivityEntry }
  | { type: 'TOGGLE_DEVICE';           payload: string }
  | { type: 'SET_DEVICE_VALUE';        payload: { id: string; prop: string; val: number } }
  | { type: 'SET_DEVICE_TYPE';         payload: { type: DeviceType; state: boolean; room?: string } }
  | { type: 'SET_DEVICES_FROM_BACKEND'; payload: Record<string, any> }
  | { type: 'TRIGGER_SOS';             payload: string }
  | { type: 'CANCEL_SOS' }
  | { type: 'INC_CONVERSATIONS' }
  | { type: 'SET_SYSTEM_STATUS';       payload: { key: string; status: string; color: string } }
  | { type: 'SET_PAGE';                payload: 'dashboard' | 'analytics' }
  | { type: 'SET_LANGUAGE';            payload: LangCode }
  | { type: 'SET_FACE_EMOTION';        payload: { emotion: string; confidence: number } }
  | { type: 'SET_CAMERA_ACTIVE';       payload: boolean }

// ─── Initial Devices (mirrors smart_home_module.py DEFAULT_DEVICES) ───────────
const INITIAL_DEVICES: Record<string, Device> = {
  light_living_room: { id: 'light_living_room', name: 'Living Room Light', type: 'light', iconName: 'Lightbulb', room: 'Living Room',  state: false, brightness: 80 },
  light_bedroom:     { id: 'light_bedroom',     name: 'Bedroom Light',     type: 'light', iconName: 'Lightbulb', room: 'Bedroom',       state: false, brightness: 60 },
  fan_living_room:   { id: 'fan_living_room',   name: 'Living Room Fan',   type: 'fan',   iconName: 'Wind',      room: 'Living Room',  state: false, speed: 3 },
  fan_bedroom:       { id: 'fan_bedroom',       name: 'Bedroom Fan',       type: 'fan',   iconName: 'Wind',      room: 'Bedroom',       state: false, speed: 2 },
  tv:                { id: 'tv',                name: 'Television',        type: 'tv',    iconName: 'Tv',        room: 'Living Room',  state: false, volume: 30 },
  door_lock:         { id: 'door_lock',         name: 'Front Door Lock',   type: 'lock',  iconName: 'Lock',      room: 'Entrance',     state: true  },
}

const INITIAL_STATE: AssistantState = {
  isListening:   false,
  isSpeaking:    false,
  currentEmotion: 'neutral',
  emotionScores:  { happy: 20, calm: 70, sad: 5, anxious: 5 },
  emotionHistory: [
    { time: '10:00', happy: 65, calm: 25, sad: 10, anxious: 0 },
    { time: '11:00', happy: 75, calm: 20, sad:  5, anxious: 0 },
    { time: '12:00', happy: 80, calm: 15, sad:  5, anxious: 0 },
    { time: '13:00', happy: 70, calm: 20, sad: 10, anxious: 0 },
    { time: '14:00', happy: 85, calm: 10, sad:  5, anxious: 0 },
    { time: '15:00', happy: 90, calm:  8, sad:  2, anxious: 0 },
  ],
  faceEmotion: null,
  faceConfidence: 0,
  cameraActive: false,
  sosActive:   false,
  sosAlertId:  null,
  messages: [
    {
      id: '0',
      text: "Good day! I'm AVIRA, your personal care assistant. 👋 I'm ready to help you with music, appliances, the time, or just a friendly chat. If you ever need urgent help, press the red SOS button. How can I help you today?",
      sender: 'ai',
      timestamp: new Date(),
    },
  ],
  activityLog: [
    { id: '0', text: 'AVIRA system initialised and ready', type: 'system', timestamp: new Date() },
  ],
  devices: INITIAL_DEVICES,
  stats: { conversations: 0, alertsToday: 0, healthScore: 95, devicesOn: 1 },
  userName: 'Ribhav',
  systemStatus: {
    voice:      { label: 'Voice Input',    status: 'Available', color: 'emerald' },
    tts:        { label: 'Text-to-Speech', status: 'Active',    color: 'blue'    },
    smartHome:  { label: 'Smart Home',     status: 'Simulated', color: 'purple'  },
    sos:        { label: 'SOS System',     status: 'Ready',     color: 'cyan'    },
    camera:     { label: 'Face Emotion',   status: 'Starting…', color: 'amber'   },
    internet:   { label: 'Internet',       status: 'Online',    color: 'emerald' },
  },
  activePage: 'dashboard',
  currentLanguage: (typeof window !== 'undefined' ? localStorage.getItem('avira_lang') as LangCode : null) || DEFAULT_LANG,
}

// ─── Reducer ──────────────────────────────────────────────────────────────────
function countOn(devices: Record<string, Device>) {
  return Object.values(devices).filter(d => d.state).length
}


function reducer(state: AssistantState, action: Action): AssistantState {
  switch (action.type) {

    case 'SET_LISTENING': return { ...state, isListening: action.payload }
    case 'SET_SPEAKING':  return { ...state, isSpeaking:  action.payload }
    case 'SET_FACE_EMOTION': 
      if (state.faceEmotion === action.payload.emotion && Math.abs(state.faceConfidence - action.payload.confidence) < 0.01) return state
      return { ...state, faceEmotion: action.payload.emotion, faceConfidence: action.payload.confidence }
    case 'SET_CAMERA_ACTIVE': return { ...state, cameraActive: action.payload }

    case 'SET_EMOTION': {
      const now    = new Date()
      const entry  = {
        time:    now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        happy:   action.payload.scores.happy,
        calm:    action.payload.scores.calm,
        sad:     action.payload.scores.sad,
        anxious: action.payload.scores.anxious,
      }
      return {
        ...state,
        currentEmotion: action.payload.emotion,
        emotionScores:  action.payload.scores,
        emotionHistory: [...state.emotionHistory.slice(-9), entry],
      }
    }

    case 'ADD_MESSAGE':
      return { ...state, messages: [...state.messages, action.payload].slice(-50) }

    case 'ADD_LOG':
      return { ...state, activityLog: [...state.activityLog, action.payload].slice(-50) }

    case 'TOGGLE_DEVICE': {
      const d = state.devices[action.payload]
      if (!d) return state
      const devices = { ...state.devices, [action.payload]: { ...d, state: !d.state, lastToggled: Date.now() } }
      return { ...state, devices, stats: { ...state.stats, devicesOn: countOn(devices) } }
    }

    case 'SET_DEVICE_VALUE': {
      const d = state.devices[action.payload.id]
      if (!d) return state
      return {
        ...state,
        devices: { ...state.devices, [action.payload.id]: { ...d, [action.payload.prop]: action.payload.val, lastToggled: Date.now() } },
      }
    }

    case 'SET_DEVICE_TYPE': {
      const updated = { ...state.devices }
      const now = Date.now()
      for (const key of Object.keys(updated)) {
        const d = updated[key]
        if (d.type !== action.payload.type) continue
        if (action.payload.room && !d.room.toLowerCase().includes(action.payload.room.toLowerCase())) continue
        updated[key] = { ...d, state: action.payload.state, lastToggled: now }
      }
      return { ...state, devices: updated, stats: { ...state.stats, devicesOn: countOn(updated) } }
    }

    case 'SET_DEVICES_FROM_BACKEND': {
      // Merge real backend states into frontend device map
      const currentDevices = state.devices
      const backendPayload = action.payload as Record<string, any>
      let hasChanged = false
      const merged = { ...currentDevices }
      const now = Date.now()

      for (const [id, backendDevice] of Object.entries(backendPayload)) {
        const currentDev = merged[id]
        if (currentDev) {
          // Cooldown check: if the device was toggled locally in the last 4 seconds, ignore server sync to prevent flicker
          if (currentDev.lastToggled && (now - currentDev.lastToggled < 4000)) {
            continue
          }

          const newState = (backendDevice as any).state ?? currentDev.state
          const newBrightness = (backendDevice as any).brightness ?? currentDev.brightness
          const newSpeed = (backendDevice as any).speed ?? currentDev.speed
          const newVolume = (backendDevice as any).volume ?? currentDev.volume
          const newValue = (backendDevice as any).value ?? currentDev.value

          if (
            currentDev.state !== newState ||
            currentDev.brightness !== newBrightness ||
            currentDev.speed !== newSpeed ||
            currentDev.volume !== newVolume ||
            currentDev.value !== newValue
          ) {
            merged[id] = {
              ...currentDev,
              state: newState,
              brightness: newBrightness,
              speed: newSpeed,
              volume: newVolume,
              value: newValue
            }
            hasChanged = true
          }
        }
      }

      if (!hasChanged) return state

      return { ...state, devices: merged, stats: { ...state.stats, devicesOn: countOn(merged) } }
    }

    case 'TRIGGER_SOS':
      return {
        ...state,
        sosActive:  true,
        sosAlertId: action.payload,
        stats: { ...state.stats, alertsToday: state.stats.alertsToday + 1 },
      }

    case 'CANCEL_SOS':
      return { ...state, sosActive: false, sosAlertId: null }

    case 'INC_CONVERSATIONS':
      return { ...state, stats: { ...state.stats, conversations: state.stats.conversations + 1 } }

    case 'SET_SYSTEM_STATUS': {
      const { key, status, color } = action.payload
      const current = state.systemStatus[key]
      if (current && current.status === status && current.color === color) return state
      
      return {
        ...state,
        systemStatus: {
          ...state.systemStatus,
          [key]: { ...state.systemStatus[key], status, color },
        },
      }
    }

    case 'SET_PAGE':
      return { ...state, activePage: action.payload }

    case 'SET_LANGUAGE': {
      if (typeof window !== 'undefined') localStorage.setItem('avira_lang', action.payload)
      return { ...state, currentLanguage: action.payload }
    }

    default: return state
  }
}

// ─── Emotion Score Mapper — converts a DistilBERT label to UI scores ──────────
export function emotionToScores(emotion: EmotionType): EmotionScores {
  switch (emotion) {
    case 'joy':      return { happy: 85, calm: 10, sad: 3, anxious: 2 }
    case 'love':     return { happy: 75, calm: 20, sad: 3, anxious: 2 }
    case 'sadness':  return { happy: 5,  calm: 10, sad: 75, anxious: 10 }
    case 'anger':    return { happy: 5,  calm: 5,  sad: 15, anxious: 75 }
    case 'fear':     return { happy: 3,  calm: 5,  sad: 12, anxious: 80 }
    case 'surprise': return { happy: 40, calm: 15, sad: 5,  anxious: 40 }
    default:         return { happy: 20, calm: 65, sad: 8,  anxious: 7 }
  }
}

// ─── Legacy keyword fallback (only for optimistic UI before backend responds) ─
export function detectEmotion(text: string): { emotion: EmotionType; scores: EmotionScores } {
  const t = text.toLowerCase()
  const isJoy      = ['happy','great','wonderful','fantastic','excited','joy','excellent','amazing','awesome','good','fine','well'].some(w => t.includes(w))
  const isSadness  = ['sad','unhappy','depressed','lonely','miss','grief','crying','hurt','pain','terrible','awful','sick','upset','worry','horrible'].some(w => t.includes(w))
  const isFear     = ['worried','nervous','anxious','scared','afraid','fear','panic','stress','tense','uneasy'].some(w => t.includes(w))
  const isAnger    = ['angry','mad','furious','annoyed','irritated','frustrated','hate'].some(w => t.includes(w))
  
  let emotion: EmotionType = 'neutral'
  if (isJoy) emotion = 'joy'
  else if (isSadness) emotion = 'sadness'
  else if (isFear) emotion = 'fear'
  else if (isAnger) emotion = 'anger'

  return { emotion, scores: emotionToScores(emotion) }
}

// ─── Command Processor — uses Backend DistilBERT model for real emotion ───────
export async function processCommand(
  text: string,
  dispatch: React.Dispatch<Action>,
  speak: (t: string) => void,
  emotion: EmotionType,
  language: LangCode = 'en',
) {
  const t = text.toLowerCase().trim()

  const log = (txt: string, type: LogType) =>
    dispatch({ type: 'ADD_LOG', payload: { id: `${Date.now()}`, text: txt, type, timestamp: new Date() } })

  const reply = (msg: string, logText?: string) => {
    dispatch({ type: 'ADD_MESSAGE', payload: { id: `${Date.now()}`, text: msg, sender: 'ai', timestamp: new Date(), emotion } })
    speak(msg)
    if (logText) log(logText, 'command')
    dispatch({ type: 'INC_CONVERSATIONS' })
  }

  // ── 1. Emergency (highest priority) ────────────────────────────────────────
  if (/\b(help me|emergency|sos|call help|i need help|falling|fell|chest pain|can'?t breathe|\u092e\u0926\u0926|\u092e\u0926\u0924 \u0915\u0930\u093e)\b/.test(t)) {
    const alertId = `SOS-${new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)}-001`
    dispatch({ type: 'TRIGGER_SOS', payload: alertId })
    log(`SOS TRIGGERED — ${alertId}`, 'sos')
    const sosMsg = language === 'hi' ? '\u0906\u092a\u093e\u0924\u0915\u093e\u0932\u0940\u0928 \u0905\u0932\u0930\u094d\u091f! \u092e\u0948\u0902 \u0906\u092a\u0915\u0947 \u0926\u0947\u0916\u092d\u093e\u0932\u0915\u0930\u094d\u0924\u093e \u0915\u094b \u0938\u0942\u091a\u093f\u0924 \u0915\u0930 \u0930\u0939\u0940 \u0939\u0942\u0901\u0964 \u0936\u093e\u0902\u0924 \u0930\u0939\u0947\u0902, \u092e\u0926\u0926 \u0906 \u0930\u0939\u0940 \u0939\u0948!'
      : language === 'mr' ? '\u0906\u0923\u0940\u092c\u093e\u0923\u0940 \u0905\u0932\u0930\u094d\u091f! \u092e\u0940 \u0924\u0941\u092e\u091a\u094d\u092f\u093e \u0915\u093e\u0933\u091c\u0940\u0935\u093e\u0939\u0915\u093e\u0932\u093e \u0938\u0942\u091a\u093f\u0924 \u0915\u0930\u0924 \u0906\u0939\u0947\u0964 \u0936\u093e\u0902\u0924 \u0930\u0939\u093e, \u092e\u0926\u0924 \u092f\u0947\u0924 \u0906\u0939\u0947!'
      : 'Emergency alert triggered! I am notifying your caregiver right now. Please stay calm. Help is on the way!'
    speak(sosMsg)
    return
  }

  // ── 2. Backend API — DistilBERT Emotion + Groq/Ollama LLM ─────────────────
  try {
    let res: any = null
    const payload = { text: text, language: language }

    // Try primary API URL first (dynamic hostname for mobile access)
    try {
      res = await axios.post(`${API_URL}/api/process`, payload, { timeout: 35000 })
    } catch (primaryErr) {
      console.warn('Primary API failed, trying localhost fallback...', primaryErr)
      // Fallback to localhost (for when accessing from the same machine with no network)
      try {
        res = await axios.post('http://127.0.0.1:5000/api/process', payload, { timeout: 35000 })
      } catch (fallbackErr) {
        console.error('Localhost fallback also failed:', fallbackErr)
        throw fallbackErr
      }
    }

    const { response, action, emotion: backendEmotion, url, backend: usedBackend } = res.data

    // ── Handle URL redirection (opening tabs/apps) ─────────────────────────
    if (url) {
      console.log("Opening URL from backend:", url)
      window.open(url, '_blank')
    }

    // ── USE THE MODEL'S EMOTION (DistilBERT) as the primary source ──────────
    const modelEmotion: EmotionType = (backendEmotion as EmotionType) || 'neutral'
    const modelScores = emotionToScores(modelEmotion)

    // STICKY BEHAVIOR: Only update UI mood when model detects a real emotion.
    // If model says "neutral", keep the previous emotion displayed until next input.
    if (modelEmotion !== 'neutral') {
      dispatch({ type: 'SET_EMOTION', payload: { emotion: modelEmotion, scores: modelScores } })
    }
    const backendLabel = usedBackend === 'ollama' ? '🔌 Offline (Ollama)' : '☁️ Online (Groq)'
    log(`🧠 DistilBERT: ${modelEmotion.toUpperCase()} | ${backendLabel}`, 'system')

    // AI reply with the model's emotion tag (use detected emotion for the bubble)
    const bubbleEmotion = modelEmotion !== 'neutral' ? modelEmotion : emotion
    dispatch({ type: 'ADD_MESSAGE', payload: { 
      id: `ai-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`, 
      text: response, 
      sender: 'ai', 
      timestamp: new Date(), 
      emotion: bubbleEmotion 
    } })
    speak(response)
    if (action) log(`Remote: ${action}`, 'command')
    dispatch({ type: 'INC_CONVERSATIONS' })

  } catch (error) {
    console.error("Backend error:", error)
    reply("I'm having trouble connecting to my central brain. Please check the network.", 'System Error')
  }
}

// ─── Context value type ───────────────────────────────────────────────────────
interface AssistantCtx {
  state:          AssistantState
  dispatch:       React.Dispatch<Action>
  sendMessage:    (text: string) => void
  speak:          (text: string) => void
  triggerSOS:     (trigger?: 'voice' | 'button') => void
  cancelSOS:      () => void
  toggleListening: () => void
  setLanguage:    (lang: LangCode) => void
  t:              (key: string) => string
}

const Ctx = createContext<AssistantCtx | null>(null)

// ─── Provider ─────────────────────────────────────────────────────────────────
export function AssistantProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE)
  const synthRef    = useRef<SpeechSynthesis | null>(null)
  const recogRef    = useRef<any>(null)
  const vapiRef     = useRef<any>(null)
  const stateRef    = useRef(state)
  stateRef.current  = state

  useEffect(() => {
    // Initialize Vapi for optional high-quality STT (non-blocking)
    try {
      const vapi = new Vapi('b5916f46-6c9a-4fa6-8543-534106b04a70')
      vapiRef.current = vapi

      vapi.on('message', (message: any) => {
        // High-quality Vapi transcript overrides browser SR result
        if (message.type === 'transcript' && message.transcriptType === 'final' && message.transcript) {
          sendMessage(message.transcript)
        }
      })

      vapi.on('error', (e: any) => {
        console.warn('Vapi unavailable, using browser SR:', e)
        vapiRef.current = null // disable Vapi so browser SR takes over
      })
    } catch (e) {
      console.warn('Vapi init failed:', e)
      vapiRef.current = null
    }
    
    // Reset backend session state on fresh frontend load
    axios.post(`${API_URL}/api/system/reset-session`).catch((e) => console.warn('Reset session failed:', e))

    synthRef.current = window.speechSynthesis
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SR) dispatch({ type: 'SET_SYSTEM_STATUS', payload: { key: 'voice', status: 'Unavailable', color: 'red' } })
  }, [])

  // ── Webcam Face Emotion Detection (every 3s) ─────────────────────────────
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)

  useEffect(() => {
    let stream: MediaStream | null = null
    let timer: ReturnType<typeof setInterval> | null = null
    let unmounted = false

    async function startCamera() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 320, height: 240, facingMode: 'user' }
        })
        // Create hidden video element
        const video = document.createElement('video')
        video.srcObject = stream
        video.setAttribute('playsinline', 'true')
        video.muted = true
        await video.play()
        videoRef.current = video

        // Create offscreen canvas for frame capture
        const canvas = document.createElement('canvas')
        canvas.width = 320
        canvas.height = 240
        canvasRef.current = canvas

        if (!unmounted) {
          dispatch({ type: 'SET_CAMERA_ACTIVE', payload: true })
          dispatch({ type: 'SET_SYSTEM_STATUS', payload: { key: 'camera', status: 'Active', color: 'emerald' } })
        }

        // Poll every 10 seconds
        timer = setInterval(() => captureAndDetect(), 10000)

      } catch (err) {
        console.warn('Webcam not available for face emotion:', err)
        if (!unmounted) {
          dispatch({ type: 'SET_CAMERA_ACTIVE', payload: false })
          dispatch({ type: 'SET_SYSTEM_STATUS', payload: { key: 'camera', status: 'Unavailable', color: 'red' } })
        }
      }
    }

    async function captureAndDetect() {
      const video = videoRef.current
      const canvas = canvasRef.current
      if (!video || !canvas || unmounted) return

      const ctx2d = canvas.getContext('2d')
      if (!ctx2d) return

      ctx2d.drawImage(video, 0, 0, 320, 240)
      let base64: string | null = canvas.toDataURL('image/jpeg', 0.7)

      try {
        const res = await axios.post(`${API_URL}/api/face-emotion`, { image: base64 })
        const data = res.data
        if (!unmounted && data.face_detected && data.confidence > 40) {
          dispatch({ type: 'SET_FACE_EMOTION', payload: { emotion: data.emotion, confidence: data.confidence } })
        }
      } catch {
        // Silently ignore — face detection is non-critical
      } finally {
        // ── Delete image data from browser memory ──────────────
        base64 = null
        ctx2d.clearRect(0, 0, 320, 240)
      }
    }

    startCamera()

    return () => {
      unmounted = true
      if (timer) clearInterval(timer)
      if (stream) stream.getTracks().forEach(t => t.stop())
      videoRef.current = null
      canvasRef.current = null
    }
  }, [])

  // ── ESP32 health check polling (every 10s) ──────────────────────────────
  useEffect(() => {
    let unmounted = false
    const poll = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/esp32/status`)
        if (unmounted) return
        if (res.data.esp32_connected) {
           dispatch({ type: 'SET_SYSTEM_STATUS', payload: { key: 'smartHome', status: 'Connected', color: 'emerald' }})
        } else {
           dispatch({ type: 'SET_SYSTEM_STATUS', payload: { key: 'smartHome', status: 'Disconnected', color: 'red' }})
        }
      } catch {
        if (!unmounted) dispatch({ type: 'SET_SYSTEM_STATUS', payload: { key: 'smartHome', status: 'Offline', color: 'zinc' }})
      }
    }
    
    // Initial check
    poll()
    // Poll every 10s
    const timer = setInterval(poll, 10000)
    return () => {
      unmounted = true
      clearInterval(timer)
    }
  }, [])

  // ── Poll real device states from backend every 3s ────────────────────
  useEffect(() => {
    let unmounted = false
    const syncDevices = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/devices`)
        if (unmounted) return
        // Backend may return { devices: {...} } or just { id: {...}, ... }
        const raw = res.data?.devices ?? res.data
        if (raw && typeof raw === 'object') {
          dispatch({ type: 'SET_DEVICES_FROM_BACKEND', payload: raw })
        }
      } catch {
        // silently ignore — backend may be temporarily busy
      }
    }
    syncDevices() // immediate first fetch
    const timer = setInterval(syncDevices, 3000)
    return () => { unmounted = true; clearInterval(timer) }
  }, [])

  // ── speak() — SOOTHING WEBSITE-BASED VOICE ────────────────────────────────
  const speak = useCallback(async (text: string) => {
    const clean = text.replace(/[\u{1F300}-\u{1FFFF}]|[\u2600-\u27BF]/gu, '').trim()
    if (!clean) return
    dispatch({ type: 'SET_SPEAKING', payload: true })

    const lang = stateRef.current.currentLanguage

    // ── 1. Hindi / Marathi → OpenAI TTS (Highest realism) ──────────────────
    if (lang === 'hi' || lang === 'mr') {
      try {
        const res = await axios.post(`${API_URL}/api/tts`, { text: clean, language: lang })
        const { audio } = res.data
        if (audio) {
          const binary  = atob(audio); const bytes = new Uint8Array(binary.length)
          for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
          const url = URL.createObjectURL(new Blob([bytes], { type: 'audio/mpeg' }))
          const audioEl = new Audio(url)
          audioEl.onended = () => { URL.revokeObjectURL(url); dispatch({ type: 'SET_SPEAKING', payload: false }) }
          audioEl.play(); return
        }
      } catch (e) { console.warn('OpenAI TTS fallback to browser', e) }
    }

    // ── 2. English → Enhanced Browser Voice (Soothing & Realistic) ──────────
    const synth = window.speechSynthesis
    if (!synth) { dispatch({ type: 'SET_SPEAKING', payload: false }); return }
    synth.cancel()

    const utter  = new SpeechSynthesisUtterance(clean)
    utter.lang   = lang === 'hi' ? 'hi-IN' : lang === 'mr' ? 'mr-IN' : 'en-IN'
    
    // SOOTHING SETTINGS: Slightly slower and lower pitch for warmth
    utter.rate   = 0.88  // Slower is more calming
    utter.pitch  = 0.95  // Slightly lower pitch sounds more mature/realistic
    utter.volume = 1.0

    const pickVoice = () => {
      const voices = synth.getVoices()
      // We prioritize "Natural" or "Google" voices as they are more realistic
      const tests = [
        (v: SpeechSynthesisVoice) => v.name.includes('Aria') && v.name.includes('Natural'),
        (v: SpeechSynthesisVoice) => v.name.includes('Natural') && v.lang.includes('en-GB'),
        (v: SpeechSynthesisVoice) => v.name.includes('Google UK English Female'),
        (v: SpeechSynthesisVoice) => v.name.includes('Google US English'),
        (v: SpeechSynthesisVoice) => v.name.includes('Microsoft Zira'),
        (v: SpeechSynthesisVoice) => v.lang.startsWith('en'),
      ]
      for (const test of tests) {
        const match = voices.find(test)
        if (match) return match
      }
      return null
    }

    const assignAndSpeak = () => {
      const voice = pickVoice()
      if (voice) utter.voice = voice
      utter.onend   = () => dispatch({ type: 'SET_SPEAKING', payload: false })
      utter.onerror = () => dispatch({ type: 'SET_SPEAKING', payload: false })
      synth.speak(utter)
    }

    if (synth.getVoices().length > 0) {
      assignAndSpeak()
    } else {
      synth.onvoiceschanged = () => { synth.onvoiceschanged = null; assignAndSpeak() }
    }
  }, [])

  // ── sendMessage() — runs emotion detection then command processor ───────────
  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim()) return
    const { emotion, scores } = detectEmotion(text)
    const lang = stateRef.current.currentLanguage
    
    dispatch({ type: 'ADD_MESSAGE', payload: { id: `${Date.now()}u`, text, sender: 'user', timestamp: new Date(), emotion } })
    dispatch({ type: 'ADD_LOG',     payload: { id: `${Date.now()}l`, text: `You: "${text}"`, type: 'command', timestamp: new Date() } })
    
    // Only update UI mood if it's a strong emotion (sticky behavior)
    if (emotion !== 'neutral') {
      dispatch({ type: 'SET_EMOTION', payload: { emotion, scores } })
    }
    
    await processCommand(text, dispatch, speak, emotion, lang)
  }, [speak])

  // ── triggerSOS() — Module 5: EmergencyAlertModule ──────────────────────────
  const triggerSOS = useCallback((trigger: 'voice' | 'button' = 'button') => {
    const id  = `SOS-${new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)}-001`
    dispatch({ type: 'TRIGGER_SOS', payload: id })
    dispatch({ type: 'ADD_LOG',     payload: { id: `${Date.now()}`, text: `🚨 SOS triggered (${trigger}) — ${id}`, type: 'sos', timestamp: new Date() } })
    console.warn(`[AVIRA EMERGENCY] ${id} | trigger=${trigger} | time=${new Date().toISOString()}`)
    speak('Emergency alert triggered! I am notifying your caregiver right now. Please stay calm. Help is on the way!')
    // Notify backend → caregiver portal will see it
    axios.post(`${API_URL}/api/sos/trigger`, { trigger_type: trigger }).catch(() => {})
  }, [speak])

  const cancelSOS = useCallback(() => {
    dispatch({ type: 'CANCEL_SOS' })
    dispatch({ type: 'ADD_LOG', payload: { id: `${Date.now()}`, text: 'SOS alert cancelled by user', type: 'system', timestamp: new Date() } })
    speak("Glad you're okay! The alert has been cancelled. I'm always here if you need me.")
    // Notify backend → caregiver portal will see cancellation
    axios.post(`${API_URL}/api/sos/cancel`).catch(() => {})
  }, [speak])

  // ── Sync UI with Backend Events (Caregiver Messages & Reminders) ─────────
  useEffect(() => {
    let unmounted = false;
    const pollEvents = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/frontend/events`)
        if (unmounted || !res.data.events) return
        
        for (const ev of res.data.events) {
          if (ev.type === 'CAREGIVER_MESSAGE' || ev.type === 'REMINDER_TRIGGER') {
            dispatch({ type: 'ADD_MESSAGE', payload: { id: `ev-${Date.now()}-${Math.random()}`, text: ev.text, sender: 'ai', timestamp: new Date(), emotion: 'neutral' } })
            dispatch({ type: 'ADD_LOG', payload: { id: `log-${Date.now()}-${Math.random()}`, text: ev.text, type: ev.type === 'REMINDER_TRIGGER' ? 'system' : 'command', timestamp: new Date() } })
            speak(ev.text)
          }
        }
      } catch (e) {
        // silently ignore polling errors
      }
    }

    const timer = setInterval(pollEvents, 3000)
    return () => {
      unmounted = true
      clearInterval(timer)
    }
  }, [speak])

  // ── toggleListening() — Module 1: SpeechRecognitionModule ──────────────────
  const toggleListening = useCallback(() => {
    // ── STOP if already listening ──────────────────────────────────────────
    if (stateRef.current.isListening) {
      recogRef.current?.stop()
      recogRef.current = null
      dispatch({ type: 'SET_LISTENING', payload: false })
      dispatch({ type: 'SET_SYSTEM_STATUS', payload: { key: 'voice', status: 'Available', color: 'emerald' } })
      return
    }

    // ── START: Browser Web Speech API (primary, instant, reliable) ─────────
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SR) {
      alert('Voice recognition not supported in this browser. Please use Chrome or Edge.')
      return
    }

    const rec = new SR()
    rec.lang = LANGUAGES[stateRef.current.currentLanguage]?.speechCode || 'en-IN'
    rec.continuous = false
    rec.interimResults = false

    rec.onresult = (e: any) => {
      const text = e.results[0][0].transcript
      recogRef.current = null
      dispatch({ type: 'SET_LISTENING', payload: false })
      dispatch({ type: 'SET_SYSTEM_STATUS', payload: { key: 'voice', status: 'Available', color: 'emerald' } })
      sendMessage(text)
    }

    rec.onerror = (err: any) => {
      console.warn('Speech recognition error:', err)
      recogRef.current = null
      dispatch({ type: 'SET_LISTENING', payload: false })
      dispatch({ type: 'SET_SYSTEM_STATUS', payload: { key: 'voice', status: 'Available', color: 'emerald' } })
    }

    rec.onend = () => {
      recogRef.current = null
      dispatch({ type: 'SET_LISTENING', payload: false })
      dispatch({ type: 'SET_SYSTEM_STATUS', payload: { key: 'voice', status: 'Available', color: 'emerald' } })
    }

    rec.start()
    recogRef.current = rec
    dispatch({ type: 'SET_LISTENING', payload: true })
    dispatch({ type: 'SET_SYSTEM_STATUS', payload: { key: 'voice', status: 'Listening…', color: 'cyan' } })
  }, [sendMessage])

  // ── setLanguage() — switch active language ────────────────────────────────
  const setLanguage = useCallback((lang: LangCode) => {
    dispatch({ type: 'SET_LANGUAGE', payload: lang })
    // Notify backend
    axios.post(`${API_URL}/api/set-language`, { language: lang }).catch(() => {})
  }, [])

  // ── t() — translation helper ──────────────────────────────────────────────
  const t = useCallback((key: string): string => {
    const lang = stateRef.current.currentLanguage
    return UI_STRINGS[lang]?.[key] || UI_STRINGS['en']?.[key] || key
  }, [])

  // Memoize the context value to prevent unnecessary re-renders of consuming components
  const contextValue = React.useMemo(() => ({
    state,
    dispatch,
    sendMessage,
    speak,
    triggerSOS,
    cancelSOS,
    toggleListening,
    setLanguage,
    t
  }), [state, sendMessage, speak, triggerSOS, cancelSOS, toggleListening, setLanguage, t])

  return (
    <Ctx.Provider value={contextValue}>
      {children}
    </Ctx.Provider>
  )
}

export function useAssistant() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useAssistant must be used within AssistantProvider')
  return ctx
}

// ── Convenience hook: live clock ──────────────────────────────────────────────
export function useClock() {
  const [now, setNow] = useState(new Date())
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(t)
  }, [])
  return now
}
