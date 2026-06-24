import { motion } from 'motion/react'
import { useAssistant } from '../context/AssistantContext'

const COLOR_DOT: Record<string, string> = {
  emerald: '#10b981', blue: '#3b82f6', purple: '#8b5cf6',
  cyan: '#06b6d4', red: '#ef4444', orange: '#f97316',
}

export function SystemStatus() {
  const { state, t } = useAssistant()
  const systems = Object.values(state.systemStatus)

  return (
    <motion.div className="p-6 rounded-[2rem] backdrop-blur-xl border border-white/10"
      style={{ background: 'rgba(255,255,255,0.03)', boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.1), 0 8px 32px 0 rgba(0, 0, 0, 0.3)' }}
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.4 }}>

      <h3 className="text-sm tracking-widest uppercase text-white/45 mb-4">{t('systemStatusTitle')}</h3>

      <div className="space-y-2">
        {systems.map((sys, i) => {
          const dotColor = COLOR_DOT[sys.color] ?? '#10b981'
          return (
            <motion.div key={sys.label}
              className="flex items-center justify-between p-3 rounded-xl transition-colors hover:bg-white/[0.04]"
              style={{ background: 'rgba(255,255,255,0.03)' }}
              initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: 0.5 + i * 0.07 }}
              whileHover={{ x: 4 }}>
              <span className="text-sm text-white/70">{sys.label}</span>
              <div className="flex items-center gap-2">
                <span className="text-xs" style={{ color: dotColor }}>{sys.status}</span>
                <motion.div className="w-2 h-2 rounded-full" style={{ background: dotColor }}
                  animate={{ boxShadow: [`0 0 0 0 ${dotColor}50`, `0 0 0 5px ${dotColor}00`] }}
                  transition={{ duration: 2, repeat: Infinity, delay: i * 0.15 }} />
              </div>
            </motion.div>
          )
        })}
      </div>
    </motion.div>
  )
}
