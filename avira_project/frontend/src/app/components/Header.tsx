import { motion, AnimatePresence } from 'motion/react'
import { Bell, Settings, User, Activity, Mic, MicOff, Globe } from 'lucide-react'
import { useAssistant, useClock } from '../context/AssistantContext'
import { useState } from 'react'

export function Header() {
  const { state, dispatch, toggleListening, setLanguage, t } = useAssistant()
  const now = useClock()
  const [showLangMenu, setShowLangMenu] = useState(false)

  const timeStr = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })
  const dateStr = now.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })

  return (
    <motion.header className="mb-4 sm:mb-8"
      initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
      <div className="flex flex-row items-center justify-between gap-2 flex-wrap">

        {/* ── Logo + Title + Clock ── */}
        <div className="flex items-center gap-2 sm:gap-8">
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="p-1.5 sm:p-2 bg-purple-500/10 rounded-lg">
              <Activity className="w-5 h-5 sm:w-6 sm:h-6 text-purple-500" />
            </div>
            <motion.h1 
              initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6, delay: 0.3 }}
              className="text-[1.3rem] sm:text-[1.7rem] font-semibold tracking-[0.25em] text-white/90">
              AVIRA
            </motion.h1>
          </div>

          {/* Live clock - hidden on smallest screens */}
          <motion.div className="hidden sm:flex items-center gap-3 pt-1"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }}>
            <span className="font-mono text-sm text-blue-500 font-medium">{timeStr}</span>
            <span className="text-white/20">•</span>
            <span className="text-sm text-white/40 hidden md:inline">{dateStr}</span>
          </motion.div>
        </div>

        {/* ── Page Navigation ── */}
        <div className="bg-white/5 backdrop-blur-xl p-1 rounded-2xl border border-white/10 flex gap-1 shadow-inner">
          {[
            { id: 'dashboard', label: t('dashboard') },
            { id: 'analytics', label: t('analytics') }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => dispatch({ type: 'SET_PAGE', payload: tab.id as any })}
              className={`px-3 sm:px-6 py-2 rounded-xl text-xs font-semibold transition-all ${
                state.activePage === tab.id 
                  ? 'bg-blue-500/20 text-blue-300 border border-blue-400/30 shadow-[0_0_25px_rgba(59,130,246,0.25)]' 
                  : 'text-white/40 hover:text-white/80 hover:bg-white/5'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* ── Right controls ── */}
        <div className="flex items-center gap-1.5 sm:gap-3">

          {/* Mic toggle button */}
          <motion.button onClick={toggleListening}
            className="p-2 sm:p-3 rounded-full relative transition-all"
            style={{
              background: state.isListening ? 'rgba(59,130,246,0.25)' : 'rgba(255,255,255,0.05)',
              border: state.isListening ? '1px solid rgba(59,130,246,0.8)' : '1px solid rgba(255,255,255,0.1)',
              backdropFilter: 'blur(16px)',
              boxShadow: state.isListening ? '0 0 30px rgba(59,130,246,0.3)' : '0 4px 12px rgba(0,0,0,0.1)',
            }}
            whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            title={state.isListening ? t('stopListening') : t('startListening')}>
            {state.isListening
              ? <Mic className="w-4 h-4 sm:w-5 sm:h-5 text-blue-400" />
              : <MicOff className="w-4 h-4 sm:w-5 sm:h-5 text-white/50" />}
            {state.isListening && (
              <motion.div className="absolute inset-0 rounded-full"
                style={{ border: '2px solid rgba(59,130,246,0.5)' }}
                animate={{ scale: [1, 1.3, 1], opacity: [1, 0, 1] }}
                transition={{ duration: 1.2, repeat: Infinity }} />
            )}
          </motion.button>

          {/* Language toggle button */}
          <div className="relative">
            <motion.button 
              onClick={() => setShowLangMenu(!showLangMenu)}
              className="p-2 sm:p-3 rounded-full relative bg-white/5 backdrop-blur-md border border-white/10 shadow-lg flex items-center gap-1 sm:gap-2"
              whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Globe className="w-4 h-4 text-white/60" />
              <span className="text-xs text-white/60 font-medium uppercase hidden sm:inline">{state.currentLanguage}</span>
            </motion.button>
            <AnimatePresence>
              {showLangMenu && (
                <motion.div 
                  initial={{ opacity: 0, y: 10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 10, scale: 0.95 }}
                  className="absolute top-12 right-0 w-36 bg-gray-900 border border-white/10 shadow-2xl rounded-xl z-50 overflow-hidden"
                >
                  <button onClick={() => { setLanguage('en'); setShowLangMenu(false); }} className="block w-full text-left px-4 py-3 text-sm text-white/80 hover:bg-white/10 transition-colors">English</button>
                  <button onClick={() => { setLanguage('hi'); setShowLangMenu(false); }} className="block w-full text-left px-4 py-3 text-sm text-white/80 hover:bg-white/10 transition-colors">Hindi (हिंदी)</button>
                  <button onClick={() => { setLanguage('mr'); setShowLangMenu(false); }} className="block w-full text-left px-4 py-3 text-sm text-white/80 hover:bg-white/10 transition-colors">Marathi (मराठी)</button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Bell - always visible */}
          <motion.button className="p-2 sm:p-3 rounded-full relative bg-white/5 backdrop-blur-md border border-white/10 shadow-lg"
            whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Bell className="w-4 h-4 text-white/60" />
            {state.sosActive && (
              <motion.div className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full"
                animate={{ scale: [1, 1.4, 1] }} transition={{ duration: 0.8, repeat: Infinity }} />
            )}
          </motion.button>

          {/* Activity - hidden on mobile */}
          <motion.button className="hidden sm:flex p-3 rounded-full bg-white/5 backdrop-blur-md border border-white/10 shadow-lg"
            whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Activity className="w-4 h-4 text-white/60" />
          </motion.button>

          {/* Settings - hidden on mobile */}
          <motion.button className="hidden sm:flex p-3 rounded-full bg-white/5 backdrop-blur-md border border-white/10 shadow-lg"
            whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Settings className="w-4 h-4 text-white/60" />
          </motion.button>

          {/* Profile - icon-only on mobile, full on larger screens */}
          <motion.button
            className="flex items-center gap-2 pl-1 sm:pl-2 sm:pr-5 pr-1 py-1 sm:py-1.5 rounded-full sm:ml-2 bg-white/5 backdrop-blur-md border border-white/10 shadow-lg hover:bg-white/10"
            whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)' }}>
              <User className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-white" />
            </div>
            <span className="text-sm text-white/90 hidden sm:inline">{state.userName}</span>
          </motion.button>
        </div>
      </div>
    </motion.header>
  )
}
