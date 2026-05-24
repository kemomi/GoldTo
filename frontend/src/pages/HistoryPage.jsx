import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircle, Clock, Cpu, FileText, History, MessageCircle, RefreshCw, Search, XCircle } from 'lucide-react'
import { listSessions, saveLastSessionId } from '../api/client'

const STATUS_LABELS = {
  idle: '等待中',
  building_graph: '构建图谱',
  generating_personas: '生成专家',
  simulating: '会商中',
  generating_report: '生成简报',
  completed: '已完成',
  error: '失败',
}

function StatusBadge({ status }) {
  const done = status === 'completed'
  const failed = status === 'error'
  const Icon = done ? CheckCircle : failed ? XCircle : Clock
  const color = done ? '#10b981' : failed ? '#f87171' : '#fbbf24'
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs"
      style={{ color, background: `${color}14`, border: `1px solid ${color}30` }}>
      <Icon size={12} /> {STATUS_LABELS[status] || status}
    </span>
  )
}

export default function HistoryPage() {
  const navigate = useNavigate()
  const [sessions, setSessions] = useState([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    listSessions()
      .then(d => setSessions(d.sessions || []))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    const sorted = [...sessions].sort((a, b) => (b.created_at || 0) - (a.created_at || 0))
    if (!q) return sorted
    return sorted.filter(s =>
      s.id?.toLowerCase().includes(q) ||
      s.prediction_goal?.toLowerCase().includes(q) ||
      s.status?.toLowerCase().includes(q)
    )
  }, [sessions, query])

  const openSession = (session, target = 'report') => {
    saveLastSessionId(session.id)
    navigate(`/${target}/${session.id}`)
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <History size={24} className="text-amber-400" />
          <div>
            <h1 className="text-2xl font-bold text-white">历史会话</h1>
            <p className="text-sm text-slate-500 mt-1">回看每次战略情报流程的会商、专家、简报和追问</p>
          </div>
        </div>
        <button onClick={load} className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm"
          style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#e2e8f0' }}>
          <RefreshCw size={15} /> 刷新
        </button>
      </div>

      <div className="glass-card p-4 mb-4">
        <div className="flex items-center gap-3 rounded-xl px-3 py-2"
          style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
          <Search size={16} className="text-slate-500" />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="搜索会话 ID、任务或状态..."
            className="flex-1 bg-transparent outline-none text-sm text-slate-200 placeholder:text-slate-600"
          />
        </div>
      </div>

      <div className="space-y-3">
        {loading ? (
          <div className="glass-card p-10 text-center text-slate-500">
            <div className="spinner w-5 h-5 mx-auto mb-3" /> 正在加载历史会话...
          </div>
        ) : filtered.length ? filtered.map(session => (
          <div key={session.id} className="glass-card p-4">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <div className="flex items-center gap-3 mb-2">
                  <span className="font-mono text-sm text-amber-400">{session.id}</span>
                  <StatusBadge status={session.status} />
                  <span className="text-xs text-slate-600">
                    {session.created_at ? new Date(session.created_at * 1000).toLocaleString('zh-CN') : ''}
                  </span>
                </div>
                <div className="text-slate-200 font-medium truncate">{session.prediction_goal || '未命名情报任务'}</div>
                <div className="text-xs text-slate-500 mt-2">
                  进度 {session.progress || 0}% · 专家 {session.agents?.length || 0} · 会商 {session.history_count || 0} · 轮次 {session.current_round || 0}/{session.total_rounds || 0}
                </div>
                {session.error && <div className="text-xs text-red-400 mt-2">{session.error}</div>}
              </div>
              <div className="flex flex-wrap justify-end gap-2 shrink-0">
                <button onClick={() => openSession(session, 'simulate')} className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs"
                  style={{ background: 'rgba(255,255,255,0.04)', color: '#cbd5e1' }}>
                  <Cpu size={13} /> 会商
                </button>
                <button onClick={() => openSession(session, 'report')} className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs"
                  style={{ background: 'rgba(245,158,11,0.12)', color: '#fbbf24' }}>
                  <FileText size={13} /> 简报
                </button>
                <button onClick={() => openSession(session, 'chat')} className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs"
                  style={{ background: 'rgba(255,255,255,0.04)', color: '#cbd5e1' }}>
                  <MessageCircle size={13} /> 追问
                </button>
              </div>
            </div>
          </div>
        )) : (
          <div className="glass-card p-10 text-center text-slate-500">
            暂无历史会话，完成一次战略情报流程后会显示在这里
          </div>
        )}
      </div>
    </div>
  )
}
