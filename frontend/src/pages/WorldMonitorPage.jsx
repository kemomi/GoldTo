import React, { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, CheckCircle, Filter, Globe2, Loader2, Play, RefreshCw, ShieldAlert } from 'lucide-react'
import { createSessionFromWorldMonitor, filterWorldMonitor } from '../api/client'

const DEFAULT_GOAL = '生成周大福今日海外市场战略简报，覆盖东南亚、日韩、北美、中东与澳洲。'

function SignalCard({ item, checked, onToggle, muted }) {
  const color = item.signal_type === 'risk' ? '#f87171' : item.signal_type === 'opportunity' ? '#10b981' : '#fbbf24'
  return (
    <div className={`glass-card p-4 ${muted ? 'opacity-60' : ''}`}>
      <div className="flex items-start gap-3">
        <input
          type="checkbox"
          checked={checked}
          onChange={() => onToggle(item.id)}
          className="mt-1 accent-amber-500"
        />
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <span className="text-xs px-2 py-0.5 rounded" style={{ background: `${color}18`, color }}>
              {item.market} · {item.category}
            </span>
            <span className="text-xs text-slate-500">优先级 {item.priority_score?.toFixed?.(2) ?? item.priority_score}</span>
            <span className="text-xs text-slate-500">{item.suggested_owner}</span>
          </div>
          <div className="font-semibold text-sm text-slate-100 leading-snug mb-2">{item.title}</div>
          {item.summary && <div className="text-xs text-slate-400 leading-relaxed mb-2">{item.summary}</div>}
          <div className="text-xs text-slate-500 mb-2">
            {item.source} · {item.variant}/{item.bucket} · WM {item.importance_score}
          </div>
          <div className="space-y-1">
            {(item.reasons || []).slice(0, 3).map((r, i) => (
              <div key={i} className="text-xs text-slate-500">- {r}</div>
            ))}
          </div>
          {item.url && (
            <a href={item.url} target="_blank" rel="noreferrer" className="inline-block text-xs text-amber-400/80 mt-3 hover:text-amber-300">
              打开来源
            </a>
          )}
        </div>
      </div>
    </div>
  )
}

function Section({ title, icon: Icon, items, selectedIds, onToggle, muted }) {
  if (!items.length) return null
  return (
    <section className="mb-6">
      <div className="flex items-center gap-2 mb-3">
        <Icon size={16} className="text-amber-400" />
        <h2 className="text-sm font-semibold text-slate-200">{title}</h2>
        <span className="text-xs text-slate-600">{items.length}</span>
      </div>
      <div className="grid grid-cols-2 gap-3">
        {items.map(item => (
          <SignalCard
            key={item.id}
            item={item}
            checked={selectedIds.has(item.id)}
            onToggle={onToggle}
            muted={muted}
          />
        ))}
      </div>
    </section>
  )
}

export default function WorldMonitorPage() {
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [goal, setGoal] = useState(DEFAULT_GOAL)
  const [rounds, setRounds] = useState(12)
  const [agents, setAgents] = useState(12)
  const [loading, setLoading] = useState(false)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState('')

  const allItems = useMemo(() => {
    if (!data) return []
    return [...(data.selected || []), ...(data.watchlist || []), ...(data.discarded || [])]
  }, [data])

  const selectedItems = useMemo(
    () => allItems.filter(item => selectedIds.has(item.id)),
    [allItems, selectedIds],
  )

  const load = async () => {
    setError('')
    setLoading(true)
    try {
      const result = await filterWorldMonitor()
      setData(result)
      const defaults = new Set([
        ...(result.selected || []).map(item => item.id),
        ...(result.watchlist || []).filter(item => item.priority_score >= 0.58).map(item => item.id),
      ])
      setSelectedIds(defaults)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  const toggle = id => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const start = async () => {
    if (!selectedItems.length) return setError('请至少保留一条情报')
    setError('')
    setStarting(true)
    try {
      const payload = {
        selected: selectedItems.filter(item => item.decision === 'selected'),
        watchlist: selectedItems.filter(item => item.decision !== 'selected'),
        prediction_goal: goal,
        rounds,
        agents_count: agents,
        auto_start: true,
      }
      const { session_id } = await createSessionFromWorldMonitor(payload)
      navigate(`/simulate/${session_id}`)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
      setStarting(false)
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Globe2 size={24} className="text-amber-400" />
            WorldMonitor 情报筛选
          </h1>
          <p className="text-slate-500 text-sm mt-1">从 WorldMonitor 新闻摘要中筛出周大福海外市场需要的信号，人工审核后进入会商。</p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold"
          style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#e2e8f0' }}
        >
          {loading ? <Loader2 size={15} className="spinner" /> : <RefreshCw size={15} />}
          拉取并筛选
        </button>
      </div>

      <div className="glass-card p-5 mb-6">
        <div className="grid grid-cols-4 gap-4 mb-4">
          {[
            ['总信息', data?.summary?.total ?? '-'],
            ['高优先级', data?.summary?.selected ?? '-'],
            ['待观察', data?.summary?.watchlist ?? '-'],
            ['已勾选', selectedItems.length],
          ].map(([label, value]) => (
            <div key={label} className="text-center">
              <div className="text-2xl font-bold text-white">{value}</div>
              <div className="text-xs text-slate-500">{label}</div>
            </div>
          ))}
        </div>
        <textarea
          value={goal}
          onChange={e => setGoal(e.target.value)}
          className="w-full rounded-xl px-4 py-3 text-sm resize-none outline-none"
          style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--text-primary)', minHeight: 72 }}
        />
        <div className="grid grid-cols-2 gap-4 mt-4">
          <div>
            <label className="text-xs text-slate-500">会商轮次 ({rounds})</label>
            <input type="range" min={3} max={30} value={rounds} onChange={e => setRounds(+e.target.value)} className="w-full accent-amber-500" />
          </div>
          <div>
            <label className="text-xs text-slate-500">专家 Agent ({agents})</label>
            <input type="range" min={4} max={20} value={agents} onChange={e => setAgents(+e.target.value)} className="w-full accent-amber-500" />
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 flex items-center gap-2 text-red-400 text-sm p-3 rounded-lg" style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}>
          <AlertCircle size={15} /> {error}
        </div>
      )}

      {!data && !loading && (
        <div className="glass-card p-10 text-center">
          <Filter size={32} className="mx-auto mb-3 text-slate-600" />
          <div className="text-slate-300 font-medium mb-1">等待拉取 WorldMonitor 情报</div>
          <div className="text-slate-600 text-sm">请确认 WorldMonitor 正在 localhost:3000 运行，然后点击“拉取并筛选”。</div>
        </div>
      )}

      {loading && (
        <div className="glass-card p-10 text-center text-slate-500">
          <div className="spinner w-6 h-6 mx-auto mb-3" />
          正在拉取 full / finance / commodity digest 并评分...
        </div>
      )}

      {data && (
        <>
          <Section title="高优先级：建议进入简报" icon={ShieldAlert} items={data.selected || []} selectedIds={selectedIds} onToggle={toggle} />
          <Section title="待观察：可人工勾选" icon={CheckCircle} items={data.watchlist || []} selectedIds={selectedIds} onToggle={toggle} />
          <Section title="低相关：默认丢弃" icon={AlertCircle} items={(data.discarded || []).slice(0, 12)} selectedIds={selectedIds} onToggle={toggle} muted />

          <div className="sticky bottom-4 flex justify-end">
            <button
              onClick={start}
              disabled={starting || !selectedItems.length}
              className="flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold"
              style={{
                background: starting || !selectedItems.length ? 'rgba(245,158,11,0.25)' : 'linear-gradient(135deg, #f59e0b, #d97706)',
                color: starting || !selectedItems.length ? 'rgba(255,255,255,0.5)' : '#000',
                boxShadow: '0 8px 28px rgba(0,0,0,0.35)',
              }}
            >
              {starting ? <div className="spinner w-4 h-4" /> : <Play size={16} />}
              用已审核情报启动会商
            </button>
          </div>
        </>
      )}
    </div>
  )
}
