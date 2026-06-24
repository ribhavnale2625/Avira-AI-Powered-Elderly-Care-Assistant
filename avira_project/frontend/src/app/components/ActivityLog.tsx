import { motion, AnimatePresence } from 'motion/react'
import { Circle } from 'lucide-react'
import { useAssistant } from '../context/AssistantContext'

const TYPE_COLOR: Record<string, string> = {
  command: '#3b82f6',
  device:  '#10b981',
  sos:     '#ef4444',
  system:  '#8b5cf6',
}
const TYPE_LABEL: Record<string, string> = {
  command: 'CMD', device: 'IOT', sos: 'SOS', system: 'SYS',
}

import React from 'react'

export const ActivityLog = React.memo(function ActivityLog() {
  const { state, t } = useAssistant()
  const { activityLog } = state

  return (
    <motion.div className="p-6 rounded-[2rem] backdrop-blur-xl border border-white/10"
      style={{ background: 'rgba(255,255,255,0.03)', boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.1), 0 8px 32px 0 rgba(0, 0, 0, 0.3)' }}
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.5 }}>

      <h3 className="text-sm tracking-widest uppercase text-white/45 mb-4">{t('activityLog')}</h3>

      <div className="space-y-2.5 max-h-52 overflow-y-auto pr-1"
        style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(255,255,255,0.1) transparent' }}>
        <AnimatePresence initial={false}>
          {activityLog.map((entry, i) => {
            const color = TYPE_COLOR[entry.type] ?? '#fff'
            return (
              <motion.div key={entry.id}
                className="flex items-start gap-3 group"
                initial={{ opacity: 0, x: 14 }} animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.22 }}
                whileHover={{ x: 4 }}>
                <div className="flex-shrink-0 mt-1.5 flex flex-col items-center gap-0.5">
                  <motion.div
                    animate={i === 0 ? { scale: [1, 1.25, 1] } : {}}
                    transition={{ duration: 2, repeat: Infinity }}>
                    <Circle className="w-2 h-2" style={{ color, fill: color }} />
                  </motion.div>
                  <span className="text-[8px] font-mono" style={{ color, opacity: 0.6 }}>
                    {TYPE_LABEL[entry.type]}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white/75 group-hover:text-white/90 transition-colors truncate">
                    {entry.text}
                  </p>
                  <p className="text-xs text-white/30 mt-0.5">
                    {entry.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </p>
                </div>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>
    </motion.div>
  )
})
