import React, { useRef } from 'react'
import { motion } from 'motion/react'
import { Lightbulb, Wind, Tv, Lock, Home, Power } from 'lucide-react'
import { useAssistant } from '../context/AssistantContext'
import axios from 'axios'

const API_URL = window.location.protocol + '//' + window.location.hostname + ':5000'
const ICON_MAP: Record<string, any> = { Lightbulb, Wind, Tv, Lock }

const TYPE_STYLE: Record<string, { active: string; border: string; glow: string; dot: string }> = {
  light:  { active: 'rgba(251,191,36,0.14)',  border: 'rgba(251,191,36,0.45)',  glow: '#fbbf24', dot: 'bg-yellow-400' },
  fan:    { active: 'rgba(59,130,246,0.12)',   border: 'rgba(59,130,246,0.40)',  glow: '#3b82f6', dot: 'bg-blue-400'   },
  tv:     { active: 'rgba(139,92,246,0.12)',   border: 'rgba(139,92,246,0.40)',  glow: '#8b5cf6', dot: 'bg-purple-400' },
  lock:   { active: 'rgba(239,68,68,0.12)',    border: 'rgba(239,68,68,0.40)',   glow: '#ef4444', dot: 'bg-red-400'    },
  sensor: { active: 'rgba(16,185,129,0.12)',   border: 'rgba(16,185,129,0.40)',  glow: '#10b981', dot: 'bg-emerald-400'},
}

export function SmartHomeControl() {
  const { state, dispatch, t } = useAssistant()
  const debounceTimers = useRef<Record<string, NodeJS.Timeout>>({})
  const devices = Object.values(state.devices)
  const activeCount = devices.filter(d => d.state).length

  const ROOM_MAP: Record<string, string> = {
    'Living Room': t('livingRoom'),
    'Bedroom':     t('bedroom'),
    'Entrance':    t('entrance'),
  }

  const ROOMS = Array.from(new Set(devices.map(d => d.room)))

  const toggle = (id: string) => {
    const d = state.devices[id]
    if (!d) return
    const targetState = !d.state
    dispatch({ type: 'TOGGLE_DEVICE', payload: id })
    dispatch({ type: 'ADD_LOG', payload: {
      id: `${Date.now()}`,
      text: `${d.name} ${t('turned')} ${targetState ? t('on') : t('off')}`,
      type: 'device',
      timestamp: new Date(),
    }})
    // Sync to backend → caregiver portal sees device changes
    axios.post(`${API_URL}/api/devices/${id}/toggle`).catch((err) => {
      console.error(`Toggle API failed for ${id}:`, err)
    })
  }

  const setSlider = (id: string, prop: string, val: number) => {
    // 1. Optimistic UI update
    dispatch({ type: 'SET_DEVICE_VALUE', payload: { id, prop, val } })

    // 2. Clear previous debounce timer for this device
    if (debounceTimers.current[id]) {
      clearTimeout(debounceTimers.current[id])
    }

    // 3. Debounce API synchronization (250ms delay)
    debounceTimers.current[id] = setTimeout(() => {
      axios.post(`${API_URL}/api/devices/${id}/set`, { [prop]: val }).catch((err) => {
        console.error(`Slider API failed for ${id}:`, err)
      })
    }, 250)
  }

  const allLights = (on: boolean) => {
    // 1. Optimistic UI update
    dispatch({ type: 'SET_DEVICE_TYPE', payload: { type: 'light', state: on } })
    dispatch({ type: 'ADD_LOG', payload: {
      id: `${Date.now()}`,
      text: `${t('allLightsTurned')} ${on ? t('on') : t('off')}`,
      type: 'device',
      timestamp: new Date(),
    }})

    // 2. Synchronize to backend by setting state for each light device
    const lights = Object.values(state.devices).filter(d => d.type === 'light')
    for (const light of lights) {
      if (light.state !== on) {
        axios.post(`${API_URL}/api/devices/${light.id}/set`, { state: on }).catch((err) => {
          console.error(`AllLights API failed for ${light.id}:`, err)
        })
      }
    }
  }

  return (
    <motion.div className="p-6 rounded-[2rem] backdrop-blur-xl border border-white/10"
      style={{ background: 'rgba(255,255,255,0.03)', boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.1), 0 8px 32px 0 rgba(0, 0, 0, 0.3)' }}
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.2 }}>

      {/* Header row */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Home className="w-4 h-4 text-white/40" />
          <h3 className="text-lg tracking-wide text-white/90">{t('smartHomeTitle')}</h3>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs px-3 py-1 rounded-full"
            style={{ background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.3)', color: '#34d399' }}>
            {activeCount} {t('activeCount')}
          </span>
          <button onClick={() => allLights(true)}
            className="text-xs px-2.5 py-1 rounded-lg text-yellow-400 transition-all hover:opacity-80"
            style={{ background: 'rgba(251,191,36,0.1)', border: '1px solid rgba(251,191,36,0.25)' }}>
            {t('allOn')}
          </button>
          <button onClick={() => allLights(false)}
            className="text-xs px-2.5 py-1 rounded-lg text-white/50 transition-all hover:opacity-80"
            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}>
            {t('allOff')}
          </button>
        </div>
      </div>

      {/* Rooms */}
      {ROOMS.map((room, ri) => {
        const roomDevices = devices.filter(d => d.room === room)
        if (!roomDevices.length) return null
        return (
          <motion.div key={room} className="mb-6 last:mb-0"
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 + ri * 0.1 }}>

            <h4 className="text-xs text-white/35 uppercase tracking-widest mb-3">{ROOM_MAP[room] ?? room}</h4>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {roomDevices.map((device, di) => {
                const Icon   = ICON_MAP[device.iconName] ?? Power
                const style  = TYPE_STYLE[device.type] ?? TYPE_STYLE.sensor
                const isFan  = device.type === 'fan'
                const isLight = device.type === 'light'

                return (
                  <div key={device.id} className="flex flex-col">
                    <motion.button onClick={() => toggle(device.id)}
                      className="p-4 rounded-[1.25rem] text-left transition-all backdrop-blur-md"
                      style={device.state
                        ? { background: style.active, border: `1px solid ${style.border}`, boxShadow: `inset 0 1px 0 rgba(255,255,255,0.1), 0 0 20px ${style.glow}40`, borderRadius: (isLight || isFan) ? '20px 20px 0 0' : 20 }
                        : { background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', borderRadius: 20 }}
                      whileHover={{ scale: 1.04, y: -2 }}
                      whileTap={{ scale: 0.96 }}>

                      {/* Icon row */}
                      <div className="flex items-start justify-between mb-2.5">
                        <motion.div
                          animate={isFan && device.state ? { rotate: 360 } : {}}
                          transition={isFan && device.state ? { duration: 1.8, repeat: Infinity, ease: 'linear' } : {}}>
                          <Icon className="w-5 h-5" style={{ color: device.state ? style.glow : 'rgba(255,255,255,0.3)' }} />
                        </motion.div>
                        <motion.div className={`w-2 h-2 rounded-full ${device.state ? style.dot : 'bg-white/15'}`}
                          animate={device.state ? { boxShadow: [`0 0 0 0 ${style.glow}60`, `0 0 0 5px ${style.glow}00`] } : {}}
                          transition={{ duration: 1.8, repeat: Infinity }} />
                      </div>

                      <p className="text-xs text-white/80 font-medium leading-tight">{device.name}</p>
                      {device.value && (
                        <p className="text-xs mt-0.5" style={{ color: device.state ? style.glow : 'rgba(255,255,255,0.3)' }}>
                          {device.value}
                        </p>
                      )}

                      {/* Status badges */}
                      <div className="flex gap-1 mt-2.5 flex-wrap">
                        <span className={`text-[9px] px-1.5 py-0.5 rounded ${!device.state ? 'bg-white/10 text-white/60' : 'text-white/25'}`}>
                          {t('off')}
                        </span>
                        {device.type === 'lock' ? (
                          <span className={`text-[9px] px-1.5 py-0.5 rounded`}
                            style={{ background: device.state ? 'rgba(239,68,68,0.25)' : 'transparent', color: device.state ? '#fca5a5' : 'rgba(255,255,255,0.25)' }}>
                            {device.state ? t('locked') : t('open')}
                          </span>
                        ) : (
                          <span className={`text-[9px] px-1.5 py-0.5 rounded`}
                            style={{ background: device.state ? `${style.glow}30` : 'transparent', color: device.state ? style.glow : 'rgba(255,255,255,0.25)' }}>
                            {device.type.toUpperCase()}
                          </span>
                        )}
                      </div>
                    </motion.button>

                    {/* Brightness slider (lights) */}
                    {isLight && device.state && device.brightness !== undefined && (
                      <div className="px-3 pb-2.5 pt-1.5 rounded-b-xl"
                        style={{ background: style.active, border: `1px solid ${style.border}`, borderTop: 'none' }}>
                        <p className="text-[9px] text-white/40 mb-1">{t('brightness')} {device.brightness}%</p>
                        <input type="range" min={10} max={100} value={device.brightness}
                          onChange={e => setSlider(device.id, 'brightness', +e.target.value)}
                          className="w-full h-1 cursor-pointer rounded-full"
                          style={{ accentColor: style.glow }} />
                      </div>
                    )}

                    {/* Speed slider (fans) */}
                    {isFan && device.state && device.speed !== undefined && (
                      <div className="px-3 pb-2.5 pt-1.5 rounded-b-xl"
                        style={{ background: style.active, border: `1px solid ${style.border}`, borderTop: 'none' }}>
                        <p className="text-[9px] text-white/40 mb-1">{t('speed')} {device.speed}/5</p>
                        <input type="range" min={1} max={5} value={device.speed}
                          onChange={e => setSlider(device.id, 'speed', +e.target.value)}
                          className="w-full h-1 cursor-pointer rounded-full"
                          style={{ accentColor: style.glow }} />
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </motion.div>
        )
      })}
    </motion.div>
  )
}
