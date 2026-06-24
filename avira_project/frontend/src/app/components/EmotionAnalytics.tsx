import { motion } from 'motion/react'
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend 
} from 'recharts'
import { useAssistant } from '../context/AssistantContext'
import { TrendingUp, Activity, Users, Cloud } from 'lucide-react'

export function EmotionAnalytics() {
  const { state } = useAssistant()
  
  // Stats for the analytics header
  const topEmotion = state.currentEmotion.toUpperCase()
  const weeklyAverage = state.stats.healthScore
  
  return (
    <motion.div 
      className="space-y-6 pb-12"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      {/* Analytics Header Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 sm:p-6 rounded-[1.5rem] sm:rounded-[2.5rem] backdrop-blur-[20px] bg-[#23262e]/60" style={{ border: '1px solid rgba(142,152,255,0.1)', boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05), 0 20px 40px rgba(0,0,0,0.4)' }}>
          <div className="flex items-center gap-3 mb-2 text-[#aaaab3]">
            <Activity className="w-5 h-5 text-[#9fa7ff]" />
            <span className="text-[11px] uppercase tracking-widest font-bold">Current Mood</span>
          </div>
          <p className="text-3xl font-bold font-['Space_Grotesk'] text-[#9fa7ff] tracking-tight">{topEmotion}</p>
          <span className="inline-block mt-3 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/30">
            DistilBERT Active
          </span>
        </div>
        
        <div className="p-5 sm:p-6 rounded-[1.5rem] sm:rounded-[2.5rem] backdrop-blur-[20px] bg-[#23262e]/60" style={{ border: '1px solid rgba(142,152,255,0.1)', boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05), 0 20px 40px rgba(0,0,0,0.4)' }}>
          <div className="flex items-center gap-3 mb-2 text-[#aaaab3]">
            <TrendingUp className="w-5 h-5 text-[#d674ff]" />
            <span className="text-[11px] uppercase tracking-widest font-bold">Mood Scores</span>
          </div>
          <div className="space-y-2 mt-2 font-['Lexend']">
            <div className="flex justify-between text-[11px] font-medium"><span className="text-[#9fa7ff]">Happy (Joy)</span><span className="text-white/80">{state.emotionScores.happy}%</span></div>
            <div className="flex justify-between text-[11px] font-medium"><span className="text-[#d674ff]">Calm (Neutral)</span><span className="text-white/80">{state.emotionScores.calm}%</span></div>
            <div className="flex justify-between text-[11px] font-medium"><span className="text-[#ff6e7f]">Stress (Anxiety)</span><span className="text-white/80">{state.emotionScores.anxious}%</span></div>
          </div>
        </div>

        <div className="p-5 sm:p-6 rounded-[1.5rem] sm:rounded-[2.5rem] backdrop-blur-[20px] bg-[#23262e]/60" style={{ border: '1px solid rgba(142,152,255,0.1)', boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05), 0 20px 40px rgba(0,0,0,0.4)' }}>
          <div className="flex items-center gap-3 mb-3 text-[#aaaab3]">
             <Cloud className="w-5 h-5 text-white/50" />
            <span className="text-[11px] uppercase tracking-widest font-bold">Vitals & Info</span>
          </div>
          <div className="flex justify-between items-end mt-2">
            <div>
              <p className="text-3xl font-bold font-['Space_Grotesk'] text-[#e7e7f0]">72</p>
              <p className="text-[10px] text-white/40 uppercase tracking-widest mt-1">BPM Heart Rate</p>
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold font-['Space_Grotesk'] text-[#e7e7f0]">98<span className="text-lg">%</span></p>
              <p className="text-[10px] text-white/40 uppercase tracking-widest mt-1">SpO2 Level</p>
            </div>
          </div>
        </div>

        <div className="p-5 sm:p-6 rounded-[1.5rem] sm:rounded-[2.5rem] backdrop-blur-[20px] flex flex-col justify-center" style={{ background: 'linear-gradient(135deg, rgba(83,97,255,0.2), rgba(187,0,252,0.2))', border: '1px solid rgba(214,116,255,0.3)', boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.1), 0 20px 40px rgba(0,0,0,0.4)' }}>
          <div className="flex items-center gap-3 mb-2 text-[#d674ff]">
            <Users className="w-6 h-6" />
            <span className="text-[11px] uppercase tracking-widest font-bold">Remote Action</span>
          </div>
          <p className="text-sm font-['Lexend'] text-white/90 leading-relaxed">
            Live view synchronized. Care logs active.
          </p>
        </div>
      </div>

      {/* Main Chart Container */}
      <div className="p-4 sm:p-10 rounded-[1.5rem] sm:rounded-[3rem] backdrop-blur-[20px] bg-[#23262e]/60" style={{ border: '1px solid rgba(142,152,255,0.1)', boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05), 0 20px 40px rgba(0, 0, 0, 0.5)' }}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 sm:mb-10 gap-4">
          <div>
            <h3 className="text-2xl sm:text-3xl font-bold font-['Space_Grotesk'] tracking-tight text-[#e7e7f0]">Emotional Telemetry</h3>
            <p className="text-xs sm:text-sm text-[#aaaab3] font-['Lexend'] mt-1 sm:mt-2">Live predictions from AVIRA emotion model — updated in real-time</p>
          </div>
          <div className="flex gap-2 self-start sm:self-auto">
            {['24H', '7D', '30D'].map(t => (
              <button key={t} className={`px-3 sm:px-5 py-1.5 sm:py-2 rounded-full text-[10px] sm:text-xs font-bold uppercase tracking-widest border transition-all ${t === '24H' ? 'bg-[#9fa7ff]/20 border-[#9fa7ff]/40 text-[#9fa7ff]' : 'bg-[#11131a] border-white/5 text-white/40 hover:bg-white/10'}`}>
                {t}
              </button>
            ))}
          </div>
        </div>

        <div className="h-[300px] sm:h-[450px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={state.emotionHistory} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorHappy" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#9fa7ff" stopOpacity={0.6}/>
                  <stop offset="95%" stopColor="#9fa7ff" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorSad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#d674ff" stopOpacity={0.5}/>
                  <stop offset="95%" stopColor="#d674ff" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorCalm" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ff6e7f" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#ff6e7f" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
              <XAxis 
                dataKey="time" 
                axisLine={false} 
                tickLine={false} 
                tick={{ fill: '#aaaab3', fontSize: 12, fontFamily: 'Lexend' }}
                dy={15}
              />
              <YAxis 
                axisLine={false} 
                tickLine={false} 
                tick={{ fill: '#aaaab3', fontSize: 12, fontFamily: 'Lexend' }}
                dx={-10}
              />
              <Tooltip 
                contentStyle={{ background: '#1d1f28', border: '1px solid rgba(142,152,255,0.2)', borderRadius: '16px', boxShadow: '0 10px 25px rgba(0,0,0,0.5)', fontFamily: 'Lexend' }}
                itemStyle={{ fontSize: '13px', fontWeight: 500 }}
              />
              <Legend verticalAlign="top" height={40} wrapperStyle={{ fontFamily: 'Lexend', fontSize: '13px', color: '#e7e7f0' }} />
              <Area type="monotone" dataKey="happy" name="Joy & Calm" stroke="#9fa7ff" fillOpacity={1} fill="url(#colorHappy)" strokeWidth={3} />
              <Area type="monotone" dataKey="calm" name="Neutral" stroke="#d674ff" fillOpacity={1} fill="url(#colorSad)" strokeWidth={3} />
              <Area type="monotone" dataKey="anxious" name="Stress" stroke="#ff6e7f" fillOpacity={1} fill="url(#colorCalm)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Footer Insights */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-5 sm:p-8 rounded-[1.5rem] sm:rounded-[3rem] backdrop-blur-[20px] bg-[#23262e]/60" style={{ border: '1px solid rgba(142,152,255,0.1)', boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05), 0 20px 40px rgba(0, 0, 0, 0.4)' }}>
          <h4 className="text-base sm:text-lg font-bold font-['Space_Grotesk'] text-[#e7e7f0] mb-4 sm:mb-6">Sentiment Distribution</h4>
          <div className="space-y-4 sm:space-y-5">
             {[
               { label: 'Positive', width: '75%', color: '#9fa7ff' },
               { label: 'Neutral', width: '20%', color: '#d674ff' },
               { label: 'Stress / Alert', width: '5%', color: '#ff6e7f' },
             ].map(bar => (
               <div key={bar.label}>
                 <div className="flex justify-between text-[10px] sm:text-xs font-bold mb-2 text-[#aaaab3] uppercase tracking-widest font-['Lexend']">
                   <span>{bar.label}</span>
                   <span>{bar.width}</span>
                 </div>
                 <div className="h-2 w-full bg-[#11131a] rounded-full overflow-hidden">
                   <div className="h-full rounded-full" style={{ width: bar.width, background: bar.color }} />
                 </div>
               </div>
             ))}
          </div>
        </div>
        <div className="p-6 sm:p-8 rounded-[1.5rem] sm:rounded-[3rem] flex flex-col justify-center items-center text-center space-y-4 backdrop-blur-[20px] bg-[#1d1f28]/80" style={{ border: '1px solid rgba(142,152,255,0.1)', boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05)' }}>
           <p className="text-xs text-[#aaaab3] font-bold uppercase tracking-widest font-['Lexend']">AI Caregiver Synopsis</p>
           <p className="text-base sm:text-xl text-[#e7e7f0] font-light leading-relaxed px-4 font-['Space_Grotesk']">
             "Everything looks balanced. Vitals are completely stable and overall mood is trending positively over the last 6 hours."
           </p>
           <button className="mt-2 sm:mt-4 px-6 sm:px-8 py-3 sm:py-4 rounded-full bg-gradient-to-r from-[#9fa7ff] to-[#8e98ff] text-[#000ba0] font-bold tracking-widest uppercase text-xs hover:shadow-[0_0_20px_rgba(159,167,255,0.4)] transition-all">
             Trigger Direct Call
           </button>
        </div>
      </div>
    </motion.div>
  )
}
