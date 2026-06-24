import { motion } from 'motion/react'
import { Clock, Calendar, Music, Youtube, Compass, Zap, Star, Cloud, Lightbulb, Tv, Lock, MicOff } from 'lucide-react'
import { useAssistant } from '../context/AssistantContext'

const COMMANDS = [
  { key: 'cmd_time',          cmd: 'what time is it',       icon: Clock,      color: '#3b82f6' },
  { key: 'cmd_date',          cmd: "what is today's date",  icon: Calendar,   color: '#8b5cf6' },
  { key: 'cmd_music',         cmd: 'play relaxing music',   icon: Music,      color: '#ec4899' },
  { key: 'cmd_youtube',       cmd: 'open youtube',          icon: Youtube,    color: '#ef4444' },
  { key: 'cmd_google',        cmd: 'open google',           icon: Compass,    color: '#f59e0b' },
  { key: 'cmd_joke',          cmd: 'tell me a joke',        icon: Zap,        color: '#f97316' },
  { key: 'cmd_funFact',      cmd: 'tell me a fun fact',    icon: Star,        color: '#06b6d4' },
  { key: 'cmd_weather',       cmd: 'open weather',          icon: Cloud,      color: '#60a5fa' },
  { key: 'cmd_hindiSongs',   cmd: 'play hindi music',      icon: Music,      color: '#a78bfa' },
  { key: 'cmd_lightsOn', cmd: 'turn on the lights',    icon: Lightbulb,  color: '#fbbf24' },
  { key: 'cmd_lightsOff',    cmd: 'turn off the lights',   icon: Lightbulb,  color: '#6b7280' },
  { key: 'cmd_tvOn',         cmd: 'turn on the tv',        icon: Tv,         color: '#8b5cf6' },
  { key: 'cmd_lockDoor',     cmd: 'lock the door',         icon: Lock,       color: '#ef4444' },
  { key: 'cmd_whatsapp',      cmd: 'open whatsapp',         icon: MicOff,     color: '#10b981' },
]

export function QuickCommands() {
  const { sendMessage, t } = useAssistant()

  return (
    <motion.div className="p-5 rounded-3xl backdrop-blur-xl"
      style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.1)', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.6 }}>

      <h3 className="text-sm tracking-widest uppercase text-white/45 mb-4">{t('quickCommands')}</h3>

      <div className="flex flex-wrap gap-2">
        {COMMANDS.map((cmd, i) => {
          const Icon = cmd.icon
          return (
            <motion.button key={cmd.key}
              onClick={() => sendMessage(cmd.cmd)}
              className="px-3 py-2 rounded-lg flex items-center gap-2 transition-all"
              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
              initial={{ opacity: 0, scale: 0.85 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.35, delay: 0.7 + i * 0.04 }}
              whileHover={{ scale: 1.06, y: -2, background: 'rgba(255,255,255,0.1)' }}
              whileTap={{ scale: 0.95 }}>
              <Icon className="w-3.5 h-3.5" style={{ color: cmd.color }} />
              <span className="text-xs text-white/70">{t(cmd.key)}</span>
            </motion.button>
          )
        })}
      </div>
    </motion.div>
  )
}
