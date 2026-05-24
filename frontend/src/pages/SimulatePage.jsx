import React, { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Cpu, Zap, Users, GitBranch, CheckCircle, AlertCircle, ArrowRight } from 'lucide-react'
import { createEventSource, getSession, saveLastSessionId } from '../api/client'

const STATUS_LABELS = {
  idle: '等待中',
  building_graph: '构建知识图谱',
  generating_personas: '生成企业专家 Agent',
  simulating: '战略情报会商中',
  generating_report: '生成战略简报',
  completed: '简报完成',
  error: '发生错误',
}

const STATUS_COLORS = {
  building_graph: '#60a5fa',
  generating_personas: '#a78bfa',
  simulating: '#fbbf24',
  generating_report: '#34d399',
  completed: '#10b981',
  error: '#f87171',
}

function StanceBar({ value }) {
  const pct = ((value + 1) / 2) * 100
  return (
    <div className="h-1.5 rounded-full w-full" style={{ background: 'rgba(255,255,255,0.08)' }}>
      <div
        className="h-full rounded-full transition-all duration-500"
        style={{
          width: `${pct}%`,
          background: value > 0.2 ? '#10b981' : value < -0.2 ? '#f87171' : '#94a3b8',
        }}
      />
    </div>
  )
}

function AgentPill({ agent }) {
  const stance = agent.current_stance
  const color = stance > 0.2 ? '#10b981' : stance < -0.2 ? '#f87171' : '#94a3b8'
  return (
    <div className="glass-card p-3 text-xs">
      <div className="flex items-center justify-between mb-2">
        <span className="font-semibold text-slate-200 truncate">{agent.name}</span>
        <span className="font-mono text-xs ml-2" style={{ color }}>{stance > 0 ? '+' : ''}{stance.toFixed(2)}</span>
      </div>
      <div className="text-slate-500 truncate mb-2">{agent.role}</div>
      <StanceBar value={stance} />
    </div>
  )
}

function InteractionLog({ items }) {
  const endRef = useRef()
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [items])

  return (
    <div className="overflow-y-auto max-h-80 space-y-2 pr-1">
      {items.map((item, i) => (
        <div key={i} className="glass-card p-3 text-xs">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-amber-400/60 font-mono">R{item.round}</span>
            <span className="text-slate-300 font-semibold">{item.agent_a}</span>
            <span className="text-slate-600">×</span>
            <span className="text-slate-300 font-semibold">{item.agent_b}</span>
          </div>
          {item.dialogue?.slice(0, 2).map((d, j) => (
            <div key={j} className="mb-1">
              <span className="text-amber-400/80">{d.speaker}: </span>
              <span className="text-slate-400">{d.text?.slice(0, 100)}{d.text?.length > 100 ? '…' : ''}</span>
            </div>
          ))}
          {item.insight && (
            <div className="mt-2 text-slate-500 italic border-l-2 border-amber-500/20 pl-2">
              洞察：{item.insight?.slice(0, 80)}…
            </div>
          )}
        </div>
      ))}
      <div ref={endRef} />
    </div>
  )
}

export default function SimulatePage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [session, setSession] = useState(null)
  const [interactions, setInteractions] = useState([])
  const [error, setError] = useState('')
  const esRef = useRef()
  const statusRef = useRef('idle')

  useEffect(() => {
    statusRef.current = session?.status || 'idle'
  }, [session?.status])

  useEffect(() => {
    saveLastSessionId(sessionId)
    // Load initial state
    getSession(sessionId).then(setSession).catch(console.error)

    // Connect SSE
    const es = createEventSource(sessionId)
    esRef.current = es

    es.onmessage = e => {
      const event = JSON.parse(e.data)

      if (event.type === 'init') {
        setSession(event.data)
        if (event.data?.error) setError(event.data.error)
      } else if (event.type === 'round_end') {
        setSession(s => s ? {
          ...s,
          current_round: event.data.round,
          agents: event.data.agents,
          progress: event.data.progress,
        } : s)
      } else if (event.type === 'personas_ready') {
        setSession(s => s ? { ...s, agents: event.data.agents } : s)
      } else if (event.type === 'interaction') {
        setInteractions(prev => [...prev.slice(-49), event.data])
      } else if (event.type === 'status') {
        setSession(s => s ? { ...s, status: event.data.status } : s)
      } else if (event.type === 'completed') {
        setSession(s => s ? { ...s, status: 'completed', progress: 100, report: event.data.report, agents: event.data.agents } : s)
      } else if (event.type === 'error') {
        setError(event.data.message || event.data.detail || '会商连接或后端任务发生错误')
        setSession(s => s ? { ...s, status: 'error', error: event.data.message } : s)
      }
    }
    es.onerror = () => {
      if (!['completed', 'error'].includes(statusRef.current)) {
        setError(prev => prev || '会商事件流连接中断，请确认后端服务仍在 http://localhost:5001 运行。')
      }
    }

    return () => es.close()
  }, [sessionId])

  const progress = session?.progress ?? 0
  const status = session?.status ?? 'idle'
  const statusColor = STATUS_COLORS[status] ?? '#94a3b8'
  const agents = session?.agents ?? []

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Cpu size={24} className="text-amber-400" />
            战略情报会商控制台
          </h1>
          <p className="text-slate-500 text-sm mt-1">{session?.prediction_goal || '加载中...'}</p>
        </div>
        {status === 'completed' && (
          <div className="flex gap-3">
            <button onClick={() => navigate(`/world/${sessionId}`)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#e2e8f0' }}>
              <Users size={15} /> 专家 Agent
            </button>
            <button onClick={() => navigate(`/report/${sessionId}`)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all"
              style={{ background: 'linear-gradient(135deg, #f59e0b, #d97706)', color: '#000' }}>
              查看战略简报 <ArrowRight size={15} />
            </button>
          </div>
        )}
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
        {status === 'simulating' && session && (
          <div className="mt-2 text-xs text-slate-500 font-mono">
            会商轮次 {session.current_round} / {session.total_rounds}
          </div>
        )}
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
            { icon: Users, label: '专家 Agent', value: agents.length || '-', color: '#a78bfa' },
            { icon: GitBranch, label: '知识图谱', value: session?.graph_data?.nodes?.length ? `${session.graph_data.nodes.length} 节点` : '-', color: '#60a5fa' },
            { icon: Zap, label: '会商记录', value: interactions.length, color: '#fbbf24' },
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

        {/* Agents */}
        <div className="col-span-2">
          <h2 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
            <Users size={14} className="text-amber-400" /> 专家判断实况
          </h2>
          {agents.length > 0 ? (
            <div className="grid grid-cols-2 gap-3">
              {agents.map(a => <AgentPill key={a.id} agent={a} />)}
            </div>
          ) : (
            <div className="glass-card p-8 text-center text-slate-500 text-sm">
              {status === 'building_graph' || status === 'idle' ? '等待专家 Agent 生成...' : '暂无专家数据'}
            </div>
          )}
        </div>

        {/* Interaction log */}
        <div>
          <h2 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
            <Zap size={14} className="text-amber-400" /> 会商实况
          </h2>
          {interactions.length > 0
            ? <InteractionLog items={interactions} />
            : <div className="glass-card p-8 text-center text-slate-500 text-sm">等待会商开始...</div>
          }
        </div>
      </div>
    </div>
  )
}
