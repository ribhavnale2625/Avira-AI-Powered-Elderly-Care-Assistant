import { motion, AnimatePresence } from 'motion/react'
import { Mic, MicOff, Send, Volume2, VolumeX } from 'lucide-react'
import React, { useState, useRef, useEffect } from 'react'
import { useAssistant } from '../context/AssistantContext'

const QUICK: Array<{ label: string; cmd: string }> = [
  { label: '🕐 Time',        cmd: 'what time is it' },
  { label: '📅 Date',        cmd: "what is today's date" },
  { label: '🎵 Music',       cmd: 'play relaxing music' },
  { label: '▶️ YouTube',     cmd: 'open youtube' },
  { label: '🔍 Google',      cmd: 'open google' },
  { label: '😄 Joke',        cmd: 'tell me a joke' },
  { label: '💡 Fun Fact',    cmd: 'tell me a fun fact' },
  { label: '🌤️ Weather',    cmd: 'open weather' },
  { label: '💡 Lights ON',   cmd: 'turn on the lights' },
  { label: '🌙 Lights OFF',  cmd: 'turn off the lights' },
  { label: '📺 TV ON',       cmd: 'turn on the tv' },
  { label: '🎶 Hindi Songs', cmd: 'play hindi music' },
]

const EMOTION_AVATAR: Record<string, string> = {
  neutral: '🤖', joy: '😄', sadness: '🤗', fear: '🌿', anger: '😌', love: '❤️', surprise: '✨',
}

export const ConversationPanel = React.memo(function ConversationPanel() {
  const { state, sendMessage, toggleListening, speak } = useAssistant()
  const { messages, isListening, isSpeaking, currentEmotion } = state
  const [input, setInput]   = useState('')
  const [muted, setMuted]   = useState(false)
  const scrollRef           = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
    }
  }, [messages])

  const handleSend = () => {
    const txt = input.trim()
    if (!txt) return
    sendMessage(txt)
    setInput('')
  }

  const handleSpeak = (text: string) => { if (!muted) speak(text) }

  return (
    <motion.div className="h-full flex flex-col rounded-[2rem] overflow-hidden backdrop-blur-xl border border-white/10"
      style={{ background: 'rgba(255,255,255,0.03)', boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.1), 0 8px 32px 0 rgba(0, 0, 0, 0.3)' }}
      initial={{ opacity: 0, x: -50 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.8 }}>

      {/* Header */}
      <div className="px-4 py-4 sm:px-10 sm:py-6 border-b border-white/10 flex items-center justify-between flex-shrink-0">
        <div>
          <h3 className="text-sm tracking-wider text-white/90 font-semibold uppercase">AVIRA – Care Assistant</h3>
          <p className="text-[11px] text-white/40 mt-1 uppercase tracking-tight">Active Voice Monitoring & IoT Control</p>
        </div>
        <div className="flex items-center gap-2">
          {isSpeaking && (
            <motion.span className="text-xs px-2 py-1 rounded-full"
              style={{ background: 'rgba(59,130,246,0.15)', border: '1px solid rgba(59,130,246,0.3)', color: '#60a5fa' }}
              animate={{ opacity: [0.6, 1, 0.6] }} transition={{ duration: 1, repeat: Infinity }}>
              Speaking…
            </motion.span>
          )}
          <button onClick={() => setMuted(m => !m)}
            className="p-1.5 rounded-lg"
            style={{ background: muted ? 'rgba(239,68,68,0.15)' : 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)' }}>
            {muted ? <VolumeX className="w-4 h-4 text-red-400" /> : <Volume2 className="w-4 h-4 text-white/50" />}
          </button>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
        <AnimatePresence initial={false}>
          {messages.map(msg => (
            <motion.div key={msg.id}
              className={`flex items-end gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
              initial={{ opacity: 0, y: 14, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.28 }}>

              {/* Avatar */}
              <div className="w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-sm"
                style={msg.sender === 'ai'
                  ? { background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)' }
                  : { background: 'linear-gradient(135deg, #10b981, #06b6d4)' }}>
                {msg.sender === 'ai' ? EMOTION_AVATAR[currentEmotion] : '👤'}
              </div>

              {/* Bubble */}
              <div className="max-w-[80%]">
                <p className="text-xs text-white/40 mb-1 px-1">
                  {msg.sender === 'ai' ? 'AVIRA' : 'You'}
                </p>
                  <div className="px-5 py-3.5 rounded-[1.25rem] shadow-lg backdrop-blur-md"
                    style={msg.sender === 'user'
                      ? { background: 'linear-gradient(135deg, #2563eb, #4f46e5)', color: '#fff', borderBottomRightRadius: 6, border: '1px solid rgba(255,255,255,0.1)' }
                      : { background: 'rgba(255,255,255,0.05)', color: '#fff', borderBottomLeftRadius: 6, border: '1px solid rgba(255,255,255,0.1)' }}>
                    <p className="text-sm leading-relaxed">{msg.text}</p>
                    {msg.emotion && msg.emotion !== 'neutral' && (
                      <p className="text-[10px] text-white/40 mt-1.5 uppercase font-medium tracking-widest border-t border-white/5 pt-1.5">
                         Detection: {msg.emotion}
                      </p>
                    )}
                  </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Quick commands strip */}
      <div className="px-4 py-2 border-t border-white/5 flex-shrink-0">
        <div className="flex gap-2 overflow-x-auto pb-1"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
          {QUICK.map(q => (
            <button key={q.cmd} onClick={() => sendMessage(q.cmd)}
              className="flex-shrink-0 px-3 py-1.5 rounded-full text-xs text-white/65 whitespace-nowrap transition-all hover:text-white hover:scale-105"
              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}>
              {q.label}
            </button>
          ))}
        </div>
      </div>

      {/* Input row */}
      <div className="p-4 space-y-3 flex-shrink-0">
        <div className="flex gap-3">
          <input
            type="text" value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="Type your command…"
            className="flex-1 px-5 py-3.5 rounded-2xl text-white/90 placeholder-white/35 focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-sm transition-all bg-white/5 backdrop-blur-lg border border-white/10 shadow-inner"
            style={{ boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.2)' }} />
          <motion.button onClick={handleSend}
            className="p-3.5 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg shadow-blue-500/30"
            whileHover={{ scale: 1.08 }} whileTap={{ scale: 0.92 }}>
            <Send className="w-5 h-5 text-white" />
          </motion.button>
        </div>
      </div>
    </motion.div>
  )
})
