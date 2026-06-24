import { motion } from 'motion/react'
import { Heart, Sun, CloudRain, ShieldAlert, Zap, Sparkles, Camera, CameraOff, Eye } from 'lucide-react'
import { useAssistant } from '../context/AssistantContext'

const INSIGHTS: Record<string, { icon: any, color: string, text: string, tip: string }> = {
  joy:      { icon: Sun,        color: '#f59e0b', text: 'You seem happy!',    tip: 'Wonderful! Would you like to hear some upbeat music?' },
  sadness:  { icon: CloudRain,  color: '#6366f1', text: 'Feeling a bit low?', tip: 'I am here for you. How about a nice cup of tea?' },
  love:     { icon: Heart,      color: '#f472b6', text: 'Feeling the love!',  tip: 'That is beautiful. Shall I call your family?' },
  anger:    { icon: ShieldAlert, color: '#ef4444', text: 'Staying calm.',      tip: 'Breathe deep. I can play some soothing sounds.' },
  fear:     { icon: Zap,        color: '#fb7185', text: 'Peace is here.',     tip: 'You are safe. All systems are secure tonight.' },
  surprise: { icon: Sparkles,   color: '#22d3ee', text: 'A pleasant surprise!', tip: 'Life is full of wonder! Want to hear a fun fact?' },
  neutral:  { icon: Sparkles,   color: '#7e22ce', text: 'System Ready',       tip: 'I am monitoring your home and health. All good!' },
}

const FACE_EMOJI: Record<string, string> = {
  joy: '😊', sadness: '😢', love: '🥰', anger: '😠', fear: '😨', surprise: '😲', neutral: '😐',
}

export function MoodInsight() {
  const { state } = useAssistant()
  const emotion = state.currentEmotion || 'neutral'
  const insight = INSIGHTS[emotion] || INSIGHTS.neutral

  const faceEmotion = state.faceEmotion || null
  const faceConfidence = state.faceConfidence || 0
  const cameraActive = state.cameraActive

  return (
    <motion.div className="p-6 rounded-[2rem] backdrop-blur-xl border border-white/10 relative overflow-hidden"
      style={{ background: 'rgba(255,255,255,0.03)', boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.1), 0 8px 32px 0 rgba(0, 0, 0, 0.3)' }}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}>
      
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm tracking-widest uppercase text-white/45">Mood Insight</h3>
        <div className="flex items-center gap-2">
          <span className="text-[9px] px-1.5 py-0.5 rounded-full text-emerald-400/70 bg-emerald-500/10 border border-emerald-500/15 uppercase tracking-wider font-medium">
            DistilBERT
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full uppercase tracking-tighter"
            style={{ background: `${insight.color}20`, color: insight.color, border: `1px solid ${insight.color}30` }}>
            {emotion}
          </span>
        </div>
      </div>
      
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-2xl flex items-center justify-center"
          style={{ background: `${insight.color}20`, border: `1px solid ${insight.color}40` }}>
          <insight.icon className="w-6 h-6" style={{ color: insight.color }} />
        </div>
        <div>
          <p className="text-white font-medium">{insight.text}</p>
          <p className="text-xs text-white/40 mt-0.5">{insight.tip}</p>
        </div>
      </div>

      {/* ── Face Emotion (CNN/Webcam) ─────────────────────────────── */}
      <motion.div 
        className="mt-5 pt-4 border-t border-white/5"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}>

        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Eye className="w-3.5 h-3.5 text-white/40" />
            <span className="text-xs tracking-widest uppercase text-white/40">Face Emotion</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[9px] px-1.5 py-0.5 rounded-full text-cyan-400/70 bg-cyan-500/10 border border-cyan-500/15 uppercase tracking-wider font-medium">
              FER-2013 CNN
            </span>
            {cameraActive ? (
              <motion.div className="flex items-center gap-1"
                animate={{ opacity: [0.5, 1, 0.5] }} transition={{ repeat: Infinity, duration: 2 }}>
                <Camera className="w-3 h-3 text-emerald-400" />
                <span className="text-[9px] text-emerald-400/70">LIVE</span>
              </motion.div>
            ) : (
              <div className="flex items-center gap-1">
                <CameraOff className="w-3 h-3 text-red-400/50" />
                <span className="text-[9px] text-red-400/50">OFF</span>
              </div>
            )}
          </div>
        </div>

        {faceEmotion && cameraActive ? (
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
              style={{ 
                background: `${(INSIGHTS[faceEmotion] || INSIGHTS.neutral).color}15`, 
                border: `1px solid ${(INSIGHTS[faceEmotion] || INSIGHTS.neutral).color}30`,
              }}>
              {FACE_EMOJI[faceEmotion] || '😐'}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="text-white text-sm font-medium capitalize">{faceEmotion}</span>
                <span className="text-[10px] text-white/30">{faceConfidence.toFixed(0)}% confidence</span>
              </div>
              {/* Confidence bar */}
              <div className="mt-1.5 h-1 w-full bg-white/5 rounded-full overflow-hidden">
                <motion.div 
                  className="h-full rounded-full"
                  style={{ background: (INSIGHTS[faceEmotion] || INSIGHTS.neutral).color }}
                  initial={{ width: '0%' }}
                  animate={{ width: `${Math.min(faceConfidence, 100)}%` }}
                  transition={{ duration: 0.6 }}
                />
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-3 text-white/25">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl bg-white/5 border border-white/10">
              😐
            </div>
            <span className="text-xs">{cameraActive ? 'No face detected' : 'Camera not available'}</span>
          </div>
        )}
      </motion.div>

      {/* Visual Indicator */}
      <div className="mt-5 h-1 w-full bg-white/5 rounded-full overflow-hidden">
        <motion.div 
          className="h-full"
          style={{ background: insight.color }}
          initial={{ width: '0%' }}
          animate={{ width: emotion === 'neutral' ? '5%' : '100%' }}
          transition={{ duration: 1 }}
        />
      </div>
    </motion.div>
  )
}
