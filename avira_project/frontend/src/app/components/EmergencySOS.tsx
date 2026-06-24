import { motion, AnimatePresence } from 'motion/react'
import { AlertTriangle, Phone, Hospital, Users, CheckCircle } from 'lucide-react'
import { useAssistant } from '../context/AssistantContext'

const CONTACTS = [
  { name: 'Emergency Services', number: '100', icon: AlertTriangle, color: '#ef4444' },
  { name: 'Dr. Nale', number: null, icon: Hospital, color: '#10b981' },
  { name: 'Family', number: null, icon: Users, color: '#3b82f6' },
]

export function EmergencySOS() {
  const { state, triggerSOS, cancelSOS, t } = useAssistant()
  const { sosActive, sosAlertId } = state

  return (
    <motion.div className="p-6 rounded-[2rem] backdrop-blur-xl border relative overflow-hidden"
      style={{
        background: sosActive ? 'rgba(239,68,68,0.15)' : 'rgba(255,255,255,0.03)',
        border: `1px solid ${sosActive ? 'rgba(239,68,68,0.6)' : 'rgba(255,255,255,0.1)'}`,
        boxShadow: sosActive ? 'inset 0 1px 0 rgba(239,68,68,0.2), 0 12px 48px rgba(239,68,68,0.4)' : 'inset 0 1px 0 rgba(255,255,255,0.1), 0 8px 32px 0 rgba(0, 0, 0, 0.3)',
      }}
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.7 }}>

      {/* Active flash overlay */}
      {sosActive && (
        <motion.div className="absolute inset-0 rounded-2xl pointer-events-none"
          style={{ background: 'rgba(239,68,68,0.06)' }}
          animate={{ opacity: [0, 0.6, 0] }}
          transition={{ duration: 0.9, repeat: Infinity }} />
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm tracking-widest uppercase text-white/45">{t('emergencySosTitle')}</h3>
        <AnimatePresence>
          {sosActive && (
            <motion.div className="flex items-center gap-2 text-xs text-red-400 font-medium"
              initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}>
              <motion.div className="w-2 h-2 bg-red-500 rounded-full"
                animate={{ scale: [1, 1.5, 1] }} transition={{ duration: 0.6, repeat: Infinity }} />
              {t('activeAlert')}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Main SOS / Cancel button */}
      <motion.button
        onClick={() => sosActive ? cancelSOS() : triggerSOS('button')}
        className="w-full p-6 rounded-[1.25rem] relative overflow-hidden mb-5 backdrop-blur-md"
        style={{
          background: sosActive ? 'linear-gradient(135deg, #7f1d1d, #991b1b)' : 'linear-gradient(135deg, #ef4444, #dc2626)',
          boxShadow: sosActive ? '0 4px 48px rgba(239,68,68,0.7)' : '0 4px 24px rgba(239,68,68,0.5)',
        }}
        whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}
        animate={sosActive ? { boxShadow: ['0 4px 24px rgba(239,68,68,0.5)', '0 4px 56px rgba(239,68,68,0.9)', '0 4px 24px rgba(239,68,68,0.5)'] } : {}}
        transition={{ duration: 0.6, repeat: sosActive ? Infinity : 0 }}>

        {sosActive && (
          <motion.div className="absolute inset-0 bg-white/15 rounded-xl"
            animate={{ scale: [1, 1.6], opacity: [0.4, 0] }}
            transition={{ duration: 1, repeat: Infinity }} />
        )}

        <div className="relative z-10 flex items-center justify-center gap-3">
          {sosActive
            ? <CheckCircle className="w-7 h-7 text-white" />
            : <AlertTriangle className="w-7 h-7 text-white" />}
          <div>
            <p className="text-xl font-light text-white tracking-widest">{sosActive ? t('cancelAlert') : t('emergencySosAction')}</p>
            <p className="text-xs text-white/75 mt-0.5">
              {sosActive ? `${t('notifyingCaregivers')} ${sosAlertId?.slice(-10)}` : t('sosInstruction')}
            </p>
          </div>
        </div>
      </motion.button>

      {/* Alert ID badge */}
      <AnimatePresence>
        {sosActive && sosAlertId && (
          <motion.div className="mb-3 p-2.5 rounded-lg text-xs font-mono text-center"
            style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)', color: '#fca5a5' }}
            initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
            🚨 {sosAlertId}<br />
            <span className="text-white/40">{t('simulatedSms')}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Quick contacts */}
      <div className="space-y-1.5">
        {CONTACTS.map((c, i) => {
          const Icon = c.icon
          return (
            <motion.button key={c.name}
              className="w-full p-3 rounded-xl flex items-center gap-3 transition-all"
              style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}
              initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: 0.8 + i * 0.08 }}
              whileHover={{ scale: 1.02, background: 'rgba(255,255,255,0.08)' }}
              whileTap={{ scale: 0.97 }}>
              <div className="p-1.5 rounded-lg" style={{ background: `${c.color}18` }}>
                <Icon className="w-4 h-4" style={{ color: c.color }} />
              </div>
              <div className="flex-1 text-left">
                <p className="text-sm text-white/85">{c.name}</p>
                <p className="text-xs text-white/35">{c.number}</p>
              </div>
              <Phone className="w-3.5 h-3.5 text-white/25" />
            </motion.button>
          )
        })}
      </div>
    </motion.div>
  )
}
