import { motion } from 'motion/react'
import { useAssistant } from '../context/AssistantContext'

const EMOTION_PALETTE: Record<string, { c1: string; c2: string; label: string }> = {
  neutral:  { c1: '#7e22ce', c2: '#2e1065', label: 'READY' },
  joy:      { c1: '#f59e0b', c2: '#10b981', label: 'HAPPY 😄' },
  sadness:  { c1: '#6366f1', c2: '#a78bfa', label: 'CARING 💛' },
  fear:     { c1: '#ec4899', c2: '#f43f5e', label: 'SOOTHING 🌿' },
  anger:    { c1: '#ef4444', c2: '#f97316', label: 'CALM 🤝' },
  love:     { c1: '#f472b6', c2: '#db2777', label: 'LOVED ❤️' },
  surprise: { c1: '#22d3ee', c2: '#0891b2', label: 'INSPIRED ✨' },
}

export function AIOrb() {
  const { state, toggleListening, t } = useAssistant()
  const { isListening, isSpeaking, currentEmotion } = state
  const { c1, c2, label } = EMOTION_PALETTE[currentEmotion] ?? EMOTION_PALETTE.neutral
  const active = isListening || isSpeaking

  return (
    <div className="relative flex items-center justify-center w-72 h-72">

      {/* Outer ambient ring */}
      <motion.div className="absolute w-72 h-72 rounded-full"
        style={{ background: `radial-gradient(circle, ${c1}18 0%, ${c2}08 55%, transparent 70%)` }}
        animate={{ scale: [1, 1.3, 1], opacity: [0.3, 0.6, 0.3] }}
        transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }} />

      {/* Mid ring */}
      <motion.div className="absolute w-56 h-56 rounded-full"
        style={{ background: `radial-gradient(circle, ${c1}22 0%, ${c2}14 55%, transparent 70%)` }}
        animate={{ scale: [1, 1.2, 1], opacity: [0.4, 0.7, 0.4] }}
        transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut', delay: 0.2 }} />

      {/* Active pulse ring */}
      {active && (
        <motion.div className="absolute w-52 h-52 rounded-full"
          style={{ border: `2px solid ${c1}80` }}
          animate={{ scale: [1, 1.18, 1], opacity: [0.9, 0.1, 0.9] }}
          transition={{ duration: 1.1, repeat: Infinity }} />
      )}

      {/* ── Main clickable orb ── */}
      <motion.button
        onClick={toggleListening}
        className="relative w-44 h-44 rounded-full focus:outline-none"
        style={{
          background: `linear-gradient(135deg, ${c1} 0%, ${c2} 55%, ${c1}cc 100%)`,
          boxShadow: `0 0 55px ${c1}99, 0 0 90px ${c2}66, inset 0 0 50px rgba(255,255,255,0.2)`,
        }}
        animate={{
          scale: active ? [1, 1.08, 1] : 1,
          boxShadow: active
            ? [`0 0 55px ${c1}99, 0 0 90px ${c2}66`, `0 0 85px ${c1}cc, 0 0 130px ${c2}99`, `0 0 55px ${c1}99, 0 0 90px ${c2}66`]
            : `0 0 40px ${c1}66, 0 0 65px ${c2}44, inset 0 0 40px rgba(255,255,255,0.15)`,
        }}
        transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        whileHover={{ scale: 1.06 }}
        whileTap={{ scale: 0.94 }}>

        {/* Rotating highlight */}
        <motion.div className="absolute inset-0 rounded-full"
          style={{ background: 'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.45) 0%, transparent 55%)' }}
          animate={{ rotate: 360 }}
          transition={{ duration: 8, repeat: Infinity, ease: 'linear' }} />

        {/* Orbiting particles */}
        {[...Array(6)].map((_, i) => (
          <motion.div key={i} className="absolute w-2 h-2 rounded-full"
            style={{ left: '50%', top: '50%', background: 'rgba(255,255,255,0.7)' }}
            animate={{
              x: [0, Math.cos((i * 60 * Math.PI) / 180) * 54, 0],
              y: [0, Math.sin((i * 60 * Math.PI) / 180) * 54, 0],
              opacity: [0, 1, 0],
            }}
            transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut', delay: i * 0.5 }} />
        ))}

        {/* Centre icon */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-4xl select-none">
            {isListening ? '🎙️' : isSpeaking ? '🔊' : '🤖'}
          </span>
        </div>
      </motion.button>

      {/* Status label */}
      <motion.div className="absolute bottom-2 text-center w-full"
        animate={{ opacity: active ? [0.6, 1, 0.6] : 0.45 }}
        transition={{ duration: 1.8, repeat: Infinity }}>
        <p className="text-sm tracking-widest uppercase" style={{ color: c1 }}>
          {isListening ? t('listening') : isSpeaking ? t('speaking') : label}
        </p>
        <p className="text-xs text-white/30 mt-0.5">{t('clickToSpeak')}</p>
      </motion.div>
    </div>
  )
}
