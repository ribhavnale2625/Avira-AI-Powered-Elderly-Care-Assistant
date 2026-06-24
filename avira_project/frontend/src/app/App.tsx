import { motion } from 'motion/react'
import { Toaster, toast } from 'sonner'
import { useEffect } from 'react'

import { Header }           from './components/Header'
import { AIOrb }            from './components/AIOrb'
import { ConversationPanel }from './components/ConversationPanel'
import { SmartHomeControl } from './components/SmartHomeControl'
import { SystemStatus }     from './components/SystemStatus'
import { ActivityLog }      from './components/ActivityLog'
import { QuickCommands }    from './components/QuickCommands'
import { MoodInsight }      from './components/MoodInsight'
import { EmergencySOS }     from './components/EmergencySOS'
import { EmotionAnalytics } from './components/EmotionAnalytics'
import { AssistantProvider, useAssistant } from './context/AssistantContext'

// ─── Inner dashboard (needs access to context) ────────────────────────────────
function Dashboard() {
  const { state, speak, t } = useAssistant()

  // SOS toast
  useEffect(() => {
    if (state.sosActive) {
      toast.error('🚨 SOS', {
        description: `Alert ID: ${state.sosAlertId} — ${t('sosAlertDescription')}`,
        duration: Infinity,
      })
    } else {
      toast.dismiss()
    }
  }, [state.sosActive, state.sosAlertId])

  const footerStats = [
    { label: t('stats_conversations'), value: String(state.stats.conversations), color: '#3b82f6' },
    { label: t('stats_devices'),    value: String(state.stats.devicesOn),     color: '#10b981' },
    { label: t('stats_health'),  value: `${state.stats.healthScore}%`,     color: '#8b5cf6' },
    { label: t('stats_alerts'),  value: String(state.stats.alertsToday),   color: state.stats.alertsToday > 0 ? '#ef4444' : '#06b6d4' },
  ]

  return (
    <div className="min-h-screen w-full overflow-auto text-white relative bg-[#0c0e14]">
      {/* Decorative Aurora glow */}
      <div className="absolute top-0 right-[20%] w-[500px] h-[500px] bg-[#8aacff]/20 rounded-full blur-[150px] pointer-events-none mix-blend-screen" />
      <div className="absolute bottom-0 left-[10%] w-[600px] h-[600px] bg-[#b287fe]/15 rounded-full blur-[150px] pointer-events-none mix-blend-screen" />

      {/* ── Main content ── */}
      <div className="relative z-10 max-w-[1800px] mx-auto px-4 sm:px-8 py-4 sm:py-6">
        <Header />

        {/* Page Content Rendering */}
        {state.activePage === 'dashboard' ? (
          <>
            <div className="grid grid-cols-12 gap-6 mt-2">
              {/* Left — Orb + Conversation + Log */}
              <div className="col-span-12 lg:col-span-4 flex flex-col space-y-6 lg:-mt-8">
                <motion.div className="flex justify-center"
                  initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 1, type: 'spring' }}>
                  <AIOrb />
                </motion.div>
                <div className="h-[420px] flex flex-col">
                  <ConversationPanel />
                </div>
                <ActivityLog />
              </div>

              {/* Middle — Smart Home + SOS */}
              <div className="col-span-12 lg:col-span-5 space-y-6">
                <SmartHomeControl />
                <EmergencySOS />
              </div>

              {/* Right — Status + Commands + Mood */}
              <div className="col-span-12 lg:col-span-3 space-y-6">
                <MoodInsight />
                <SystemStatus />
                <QuickCommands />
              </div>
            </div>

            {/* Footer stats */}
            <motion.div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6"
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 1 }}>
              {footerStats.map((s, i) => (
                <motion.div key={s.label}
                  className="p-4 sm:p-5 rounded-[1.5rem] sm:rounded-[2rem] backdrop-blur-[20px] bg-[#23262e]/60"
                  style={{ boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05), 0 20px 40px rgba(0, 0, 0, 0.4)' }}
                  initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: 1.1 + i * 0.08 }}
                  whileHover={{ scale: 1.02, backgroundColor: 'rgba(35, 38, 46, 0.8)' }}>
                  <p className="text-xs sm:text-sm text-[#aaaab3] font-medium tracking-wide mb-1">{s.label}</p>
                  <p className="text-2xl sm:text-3xl font-bold font-['Space_Grotesk']" style={{ color: s.color }}>{s.value}</p>
                </motion.div>
              ))}
            </motion.div>
          </>
        ) : (
          <div className="mt-6">
            <EmotionAnalytics />
          </div>
        )}

        <motion.p className="mt-5 text-center text-xs text-white/20"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 1, delay: 1.2 }}>
          {t('footer_status')}
        </motion.p>
      </div>

      <Toaster position="top-right" theme="dark" richColors />
    </div>
  )
}

// ─── Root export ─────────────────────────────────────────────────────────────
export default function App() {
  return (
    <AssistantProvider>
      <Dashboard />
    </AssistantProvider>
  )
}
