import React, { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Cpu, Zap, Radio, CheckCircle, AlertCircle, ArrowRight, Globe, Users, FileText, Play } from 'lucide-react'
import { createEventSource, getSession, startAnalysis } from '../api/client'

const STATUS_LABELS = {
  idle: '等待中',
  collecting: '数据采集',
  analyzing: 'CrewAI 分析中',
  generating_briefing: '生成简报',
  completed: '分析完成',
  error: '发生错误',
}

const STATUS_COLORS = {
  collecting: '#60a5fa',
  analyzing: '#fbbf24',
  generating_briefing: '#34d399',
  completed: '#10b981',
  error: '#f87171',
}

export default function SimulatePage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [session, setSession] = useState(null)
  const [events, setEvents] = useState([])
  const [agentAnalyses, setAgentAnalyses] = useState([])
  const [error, setError] = useState('')
  const [starting, setStarting] = useState(false)
  const esRef = useRef()
  const analysisStarted = useRef(false)

  // Auto-start analysis helper
  const tryStartAnalysis = async (sess) => {
    if (analysisStarted.current) return
    if (!sess) return
    const canStart = sess.status === 'collecting' || sess.status === 'idle'
    const hasData = (sess.events_count || 0) > 0
    if (canStart && hasData) {
      analysisStarted.current = true
      setStarting(true)
      try {
        await startAnalysis(sessionId)
      } catch (e) {
        console.error('Start analysis failed:', e)
        setError('启动分析失败: ' + (e.response?.data?.detail || e.message))
        analysisStarted.current = false
      } finally {
        setStarting(false)
      }
    }
  }

  useEffect(() => {
    // Load initial state and try auto-start
    getSession(sessionId).then(s => {
      setSession(s)
      tryStartAnalysis(s)
    }).catch(console.error)

    // Connect SSE
    const es = createEventSource(sessionId)
    esRef.current = es

    es.onmessage = e => {
      const event = JSON.parse(e.data)

      if (event.type === 'init') {
        setSession(event.data)
        tryStartAnalysis(event.data)
      } else if (event.type === 'events_collected') {
        setEvents(event.data.events)
        setSession(s => s ? { ...s, events_count: event.data.count } : s)
        tryStartAnalysis({ ...session, events_count: event.data.count, status: 'collecting' })
      } else if (event.type === 'agent_analysis') {
        setAgentAnalyses(prev => [...prev, event.data.agent])
        setSession(s => s ? { ...s, progress: event.data.progress } : s)
      } else if (event.type === 'status') {
        setSession(s => s ? { ...s, status: event.data.status } : s)
      } else if (event.type === 'completed') {
        setSession(s => s ? { ...s, status: 'completed', progress: 100, briefing: event.data.briefing } : s)
        setAgentAnalyses(event.data.agents_analysis || [])
      } else if (event.type === 'error') {
        setError(event.data.message)
        setSession(s => s ? { ...s, status: 'error' } : s)
      }
    }
    es.onerror = () => { /* SSE reconnects automatically */ }

    return () => es.close()
  }, [sessionId, tryStartAnalysis])

  const handleManualStart = async () => {
    if (starting) return
    setStarting(true)
    setError('')
    try {
      await startAnalysis(sessionId)
      analysisStarted.current = true
    } catch (e) {
      setError('手动启动分析失败: ' + (e.response?.data?.detail || e.message))
    } finally {
      setStarting(false)
    }
  }

  const progress = session?.progress ?? 0
  const status = session?.status ?? 'idle'
  const statusColor = STATUS_COLORS[status] ?? '#94a3b8'
  const hasEvents = (session?.events_count || 0) > 0

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Cpu size={24} className="text-amber-400" />
            情报分析控制台
          </h1>
          <p className="text-slate-500 text-sm mt-1">{session?.topic || '加载中...'}</p>
        </div>
        <div className="flex gap-3">
          {status === 'completed' && (
            <button onClick={() => navigate(`/report/${sessionId}`)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all"
              style={{ background: 'linear-gradient(135deg, #f59e0b, #d97706)', color: '#000' }}>
              <FileText size={15} /> 查看简报 <ArrowRight size={15} />
            </button>
          )}
          {(status === 'idle' || status === 'collecting') && hasEvents && !analysisStarted.current && (
            <button onClick={handleManualStart} disabled={starting}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all"
              style={{ background: starting ? 'rgba(245,158,11,0.3)' : 'linear-gradient(135deg, #f59e0b, #d97706)', color: '#000', cursor: starting ? 'not-allowed' : 'pointer' }}>
              <Play size={15} /> {starting ? '启动中...' : '启动分析'}
            </button>
          )}
        </div>
      </div>

      {/* Progress */}
      <div className="glass-card p-5 mb-6">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            {status === 'completed'
              ? <CheckCircle size={18} className="text-emerald-400" />
              : status === 'error'
              ? <AlertCircle size={18} className="text-red-400" />
              : <div className="spinner w-4 h-4" />
            }
            <span className="text-sm font-medium" style={{ color: statusColor }}>
              {STATUS_LABELS[status] || status}
            </span>
          </div>
          <div className="text-sm font-mono" style={{ color: statusColor }}>{progress}%</div>
        </div>
        <div className="h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
          <div
            className={`h-full rounded-full transition-all duration-1000 ${status !== 'completed' ? 'progress-bar' : ''}`}
            style={{ width: `${progress}%`, background: status === 'completed' ? '#10b981' : undefined }}
          />
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 rounded-xl text-red-400 text-sm" style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}>
          <AlertCircle size={15} className="inline mr-2" /> {error}
        </div>
      )}

      <div className="grid grid-cols-3 gap-6">
        {/* Stats */}
        <div className="col-span-3 grid grid-cols-4 gap-4">
          {[
            { icon: Globe, label: '采集事件', value: session?.events_count ?? '-', color: '#60a5fa' },
            { icon: Users, label: 'Agent 分析', value: agentAnalyses.length || '-', color: '#a78bfa' },
            { icon: Radio, label: '数据源', value: 'WorldMonitor', color: '#fbbf24' },
            { icon: CheckCircle, label: '进度', value: `${progress}%`, color: '#10b981' },
          ].map((s, i) => (
            <div key={i} className="glass-card p-4 flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: `${s.color}15` }}>
                <s.icon size={20} style={{ color: s.color }} />
              </div>
              <div>
                <div className="text-xl font-bold text-white">{s.value}</div>
                <div className="text-xs text-slate-500">{s.label}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Events list */}
        <div className="col-span-2">
          <h2 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
            <Globe size={14} className="text-amber-400" /> 采集到的全球事件
          </h2>
          {events.length > 0 ? (
            <div className="space-y-2">
              {events.map((e, i) => (
                <div key={i} className="glass-card p-3 text-xs">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-slate-200">{e.title}</span>
                    <span className="text-amber-400/60 font-mono">{Math.round((e.relevance || 0) * 100)}% 相关</span>
                  </div>
                  <div className="text-slate-500 mb-1">{e.source} · {e.category}</div>
                  <div className="text-slate-400">{e.summary}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="glass-card p-8 text-center text-slate-500 text-sm">
              {status === 'collecting' ? '正在从 World Monitor 数据源采集事件...' : '等待数据采集'}
            </div>
          )}
        </div>

        {/* Agent analyses */}
        <div>
          <h2 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
            <Users size={14} className="text-amber-400" /> Agent 分析实况
          </h2>
          {agentAnalyses.length > 0 ? (
            <div className="space-y-3">
              {agentAnalyses.map((a, i) => (
                <div key={i} className="glass-card p-3 text-xs">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold"
                      style={{ background: 'rgba(245,158,11,0.15)', color: '#fbbf24' }}>
                      {a.name[0]}
                    </div>
                    <div>
                      <div className="text-slate-200 font-semibold">{a.name}</div>
                      <div className="text-slate-600">{a.role}</div>
                    </div>
                  </div>
                  <div className="text-slate-400 leading-relaxed">{a.insight}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="glass-card p-8 text-center text-slate-500 text-sm">
              {status === 'analyzing' ? 'CrewAI 智能体正在协同分析...' : '等待分析启动'}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
