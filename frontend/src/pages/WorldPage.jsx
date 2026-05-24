import React, { useEffect, useState, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { Globe, TrendingUp, TrendingDown, Minus, ChevronDown, ChevronUp } from 'lucide-react'
import { getAgents, getGraph, getHistory, saveLastSessionId } from '../api/client'

function StanceIcon({ value }) {
  if (value > 0.2) return <TrendingUp size={14} className="text-emerald-400" />
  if (value < -0.2) return <TrendingDown size={14} className="text-red-400" />
  return <Minus size={14} className="text-slate-400" />
}

function AgentCard({ agent, onSelect, selected }) {
  const stance = agent.current_stance
  const color = stance > 0.2 ? '#10b981' : stance < -0.2 ? '#f87171' : '#94a3b8'
  const pct = ((stance + 1) / 2) * 100

  return (
    <div
      onClick={() => onSelect(agent)}
      className={`agent-card glass-card p-4 ${selected ? 'selected' : ''}`}
      style={{ border: `1px solid ${selected ? 'rgba(245,158,11,0.6)' : 'rgba(255,255,255,0.06)'}` }}
    >
      <div className="flex items-start justify-between mb-2">
        <div>
          <div className="font-semibold text-sm text-white">{agent.name}</div>
          <div className="text-xs text-slate-500 mt-0.5">{agent.role}</div>
        </div>
        <div className="flex items-center gap-1">
          <StanceIcon value={stance} />
          <span className="text-xs font-mono" style={{ color }}>{stance > 0 ? '+' : ''}{stance.toFixed(2)}</span>
        </div>
      </div>
      <div className="text-xs text-slate-600 mb-2 truncate">{agent.organization}</div>
      <div className="h-1 rounded-full mb-3" style={{ background: 'rgba(255,255,255,0.06)' }}>
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: color }} />
      </div>
      <div className="flex justify-between text-xs text-slate-600">
          <span>会商 {agent.interaction_count} 次</span>
          <span style={{ color: color }}>
          {stance > 0.2 ? '机会' : stance < -0.2 ? '风险' : '观察'}
        </span>
      </div>
    </div>
  )
}

function AgentDetail({ agent, history }) {
  const myHistory = history.filter(h => h.agent_a_id === agent.id || h.agent_b_id === agent.id)
  const [expanded, setExpanded] = useState(null)

  return (
    <div className="glass-card p-5">
      <div className="flex items-center gap-4 mb-4">
        <div className="w-12 h-12 rounded-xl flex items-center justify-center text-xl font-bold"
          style={{ background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)', color: '#fbbf24' }}>
          {agent.name[0]}
        </div>
        <div>
          <div className="font-bold text-white">{agent.name}</div>
          <div className="text-sm text-slate-400">{agent.role} · {agent.organization}</div>
        </div>
      </div>

      <div className="space-y-3 text-sm">
        <div>
          <div className="text-xs text-slate-500 mb-1">性格特征</div>
          <div className="text-slate-300">{agent.personality}</div>
        </div>
        <div>
          <div className="text-xs text-slate-500 mb-1">动机</div>
          <div className="text-slate-300">{agent.motivation}</div>
        </div>
        {agent.expertise?.length > 0 && (
          <div>
            <div className="text-xs text-slate-500 mb-1">专业领域</div>
            <div className="flex flex-wrap gap-1.5">
              {agent.expertise.map((e, i) => (
                <span key={i} className="text-xs px-2 py-0.5 rounded" style={{ background: 'rgba(245,158,11,0.1)', color: '#fbbf24' }}>
                  {e}
                </span>
              ))}
            </div>
          </div>
        )}
        <div>
          <div className="text-xs text-slate-500 mb-1">最新洞察</div>
          <div className="space-y-1.5">
            {agent.insights?.slice(-3).map((ins, i) => (
              <div key={i} className="text-slate-400 text-xs border-l-2 border-amber-500/20 pl-2">{ins}</div>
            ))}
          </div>
        </div>
      </div>

      {/* Interaction history for this agent */}
      {myHistory.length > 0 && (
        <div className="mt-4">
          <div className="text-xs text-slate-500 mb-2">会商记录（{myHistory.length} 条）</div>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {myHistory.slice(-5).map((h, i) => {
              const partner = h.agent_a_id === agent.id ? h.agent_b : h.agent_a
              return (
                <div key={i} className="text-xs p-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)' }}>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-amber-400/60 font-mono">R{h.round}</span>
                    <span className="text-slate-500">与 {partner}</span>
                  </div>
                  <button onClick={() => setExpanded(expanded === i ? null : i)} className="text-slate-600 flex items-center gap-1">
                    {expanded === i ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                    {h.insight?.slice(0, 50)}…
                  </button>
                  {expanded === i && (
                    <div className="mt-2 space-y-1">
                      {h.dialogue?.map((d, j) => (
                        <div key={j}>
                          <span style={{ color: d.speaker === agent.name ? '#fbbf24' : '#94a3b8' }}>{d.speaker}: </span>
                          <span className="text-slate-400">{d.text}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

function GraphViz({ graphData }) {
  const canvasRef = useRef()

  useEffect(() => {
    if (!graphData?.nodes?.length) return
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const W = canvas.width = canvas.offsetWidth
    const H = canvas.height = canvas.offsetHeight

    // Simple force layout
    const nodes = graphData.nodes.map((n, i) => ({
      ...n,
      x: W * 0.1 + Math.random() * W * 0.8,
      y: H * 0.1 + Math.random() * H * 0.8,
      vx: 0, vy: 0,
    }))
    const nodeMap = Object.fromEntries(nodes.map(n => [n.id, n]))

    let frame
    const simulate = () => {
      // Repulsion
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x - nodes[i].x
          const dy = nodes[j].y - nodes[i].y
          const d = Math.sqrt(dx * dx + dy * dy) || 1
          const f = 800 / (d * d)
          nodes[i].vx -= f * dx / d; nodes[i].vy -= f * dy / d
          nodes[j].vx += f * dx / d; nodes[j].vy += f * dy / d
        }
      }
      // Attraction for edges
      for (const e of graphData.edges || []) {
        const a = nodeMap[e.source], b = nodeMap[e.target]
        if (!a || !b) continue
        const dx = b.x - a.x, dy = b.y - a.y
        const d = Math.sqrt(dx * dx + dy * dy) || 1
        const f = (d - 120) * 0.05
        a.vx += f * dx / d; a.vy += f * dy / d
        b.vx -= f * dx / d; b.vy -= f * dy / d
      }
      // Center gravity
      nodes.forEach(n => {
        n.vx += (W / 2 - n.x) * 0.003
        n.vy += (H / 2 - n.y) * 0.003
        n.x += n.vx * 0.5; n.y += n.vy * 0.5
        n.vx *= 0.85; n.vy *= 0.85
        n.x = Math.max(40, Math.min(W - 40, n.x))
        n.y = Math.max(40, Math.min(H - 40, n.y))
      })
    }

    const draw = () => {
      ctx.clearRect(0, 0, W, H)
      // Edges
      for (const e of graphData.edges || []) {
        const a = nodeMap[e.source], b = nodeMap[e.target]
        if (!a || !b) continue
        ctx.beginPath()
        ctx.moveTo(a.x, a.y)
        ctx.lineTo(b.x, b.y)
        ctx.strokeStyle = 'rgba(245,158,11,0.15)'
        ctx.lineWidth = 1
        ctx.stroke()
      }
      // Nodes
      nodes.forEach(n => {
        const imp = n.importance || 0.5
        const r = 6 + imp * 10
        ctx.beginPath()
        ctx.arc(n.x, n.y, r, 0, Math.PI * 2)
        ctx.fillStyle = 'rgba(245,158,11,0.25)'
        ctx.fill()
        ctx.strokeStyle = 'rgba(245,158,11,0.6)'
        ctx.lineWidth = 1.5
        ctx.stroke()
        ctx.fillStyle = '#f1f5f9'
        ctx.font = `${Math.max(9, 10 + imp * 2)}px Inter`
        ctx.textAlign = 'center'
        ctx.fillText(n.name?.slice(0, 8) || n.id, n.x, n.y + r + 12)
      })
    }

    const loop = () => {
      simulate()
      draw()
      frame = requestAnimationFrame(loop)
    }
    loop()
    return () => cancelAnimationFrame(frame)
  }, [graphData])

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-full"
      style={{ display: 'block' }}
    />
  )
}

export default function WorldPage() {
  const { sessionId } = useParams()
  const [agents, setAgents] = useState([])
  const [graphData, setGraphData] = useState(null)
  const [history, setHistory] = useState([])
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [tab, setTab] = useState('agents')

  useEffect(() => {
    saveLastSessionId(sessionId)
    getAgents(sessionId).then(d => { setAgents(d.agents); setSelectedAgent(d.agents[0]) }).catch(console.error)
    getGraph(sessionId).then(d => setGraphData(d.graph)).catch(console.error)
    getHistory(sessionId, { limit: 200 }).then(d => setHistory(d.history)).catch(console.error)
  }, [sessionId])

  const avgStance = agents.length ? agents.reduce((s, a) => s + a.current_stance, 0) / agents.length : 0
  const bullish = agents.filter(a => a.current_stance > 0.2).length
  const bearish = agents.filter(a => a.current_stance < -0.2).length

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Globe size={24} className="text-amber-400" />
        <h1 className="text-2xl font-bold text-white">企业专家 Agent</h1>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: '平均判断', value: `${avgStance > 0 ? '+' : ''}${avgStance.toFixed(3)}`, color: avgStance > 0 ? '#10b981' : '#f87171' },
          { label: '机会导向', value: `${bullish} 人`, color: '#10b981' },
          { label: '风险警惕', value: `${bearish} 人`, color: '#f87171' },
          { label: '中性观察', value: `${agents.length - bullish - bearish} 人`, color: '#94a3b8' },
        ].map((s, i) => (
          <div key={i} className="glass-card p-4 text-center">
            <div className="text-2xl font-bold mb-1" style={{ color: s.color }}>{s.value}</div>
            <div className="text-xs text-slate-500">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-6 border-b mb-6" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
        {[['agents', '专家列表'], ['graph', '知识图谱']].map(([key, label]) => (
          <button key={key} onClick={() => setTab(key)}
            className={`pb-3 text-sm font-medium transition-all ${tab === key ? 'tab-active' : 'tab-inactive'}`}>
            {label}
          </button>
        ))}
      </div>

      {tab === 'agents' ? (
        <div className="grid grid-cols-3 gap-6">
          {/* Agent grid */}
          <div className="col-span-2 grid grid-cols-2 gap-3 content-start">
            {agents.map(a => (
              <AgentCard key={a.id} agent={a} selected={selectedAgent?.id === a.id} onSelect={setSelectedAgent} />
            ))}
          </div>
          {/* Detail panel */}
          <div>
            {selectedAgent ? (
              <AgentDetail agent={selectedAgent} history={history} />
            ) : (
              <div className="glass-card p-8 text-center text-slate-500 text-sm">点击专家 Agent 查看详情</div>
            )}
          </div>
        </div>
      ) : (
        <div className="glass-card" style={{ height: 520 }}>
          {graphData?.nodes?.length ? (
            <GraphViz graphData={graphData} />
          ) : (
            <div className="h-full flex items-center justify-center text-slate-500 text-sm">
              知识图谱数据加载中...
            </div>
          )}
        </div>
      )}
    </div>
  )
}
