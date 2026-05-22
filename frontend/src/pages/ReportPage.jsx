import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { FileText, MessageCircle, TrendingUp, TrendingDown, Users, Download } from 'lucide-react'
import { getReport, getAgents } from '../api/client'

// Simple markdown-to-JSX renderer (handles ##, **bold**, - list, > quote)
function MarkdownRenderer({ content }) {
  const lines = content.split('\n')
  const elements = []
  let i = 0

  const parseLine = str => {
    // Bold
    const parts = str.split(/\*\*(.*?)\*\*/g)
    return parts.map((p, i) => i % 2 === 1 ? <strong key={i} style={{ color: '#fbbf24' }}>{p}</strong> : p)
  }

  while (i < lines.length) {
    const line = lines[i]

    if (line.startsWith('## ')) {
      elements.push(<h2 key={i} className="text-lg font-bold mt-6 mb-2" style={{ color: '#fbbf24' }}>{line.slice(3)}</h2>)
    } else if (line.startsWith('### ')) {
      elements.push(<h3 key={i} className="text-base font-semibold mt-4 mb-2 text-slate-200">{line.slice(4)}</h3>)
    } else if (line.startsWith('# ')) {
      elements.push(<h1 key={i} className="text-2xl font-bold mt-2 mb-3" style={{ color: '#fbbf24' }}>{line.slice(2)}</h1>)
    } else if (line.startsWith('- ') || line.startsWith('* ')) {
      elements.push(<li key={i} className="ml-4 text-slate-300 text-sm mb-1">{parseLine(line.slice(2))}</li>)
    } else if (line.startsWith('> ')) {
      elements.push(
        <blockquote key={i} className="border-l-2 pl-4 my-2 text-slate-400 text-sm italic"
          style={{ borderColor: 'rgba(245,158,11,0.4)' }}>
          {parseLine(line.slice(2))}
        </blockquote>
      )
    } else if (line.trim() === '') {
      elements.push(<br key={i} />)
    } else {
      elements.push(<p key={i} className="text-slate-300 text-sm leading-relaxed mb-1">{parseLine(line)}</p>)
    }
    i++
  }
  return <div>{elements}</div>
}

function StanceChart({ agents }) {
  if (!agents.length) return null

  const buckets = { '极度悲观': 0, '悲观': 0, '中性': 0, '乐观': 0, '极度乐观': 0 }
  agents.forEach(a => {
    const s = a.current_stance
    if (s < -0.6) buckets['极度悲观']++
    else if (s < -0.2) buckets['悲观']++
    else if (s < 0.2) buckets['中性']++
    else if (s < 0.6) buckets['乐观']++
    else buckets['极度乐观']++
  })

  const colors = ['#f87171', '#fb923c', '#94a3b8', '#4ade80', '#10b981']
  const max = Math.max(...Object.values(buckets), 1)

  return (
    <div className="glass-card p-4">
      <div className="text-xs font-semibold text-slate-400 mb-4 flex items-center gap-2">
        <Users size={12} /> 智能体立场分布
      </div>
      <div className="space-y-2">
        {Object.entries(buckets).map(([label, count], i) => (
          <div key={label} className="flex items-center gap-3 text-xs">
            <div className="w-16 text-right text-slate-500">{label}</div>
            <div className="flex-1 h-5 rounded" style={{ background: 'rgba(255,255,255,0.04)' }}>
              <div className="h-full rounded transition-all"
                style={{ width: `${(count / max) * 100}%`, background: colors[i], minWidth: count > 0 ? 4 : 0 }} />
            </div>
            <div className="w-6 text-slate-400 font-mono">{count}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function StanceTimeline({ agents }) {
  if (!agents.length) return null
  const avg = agents.reduce((s, a) => s + a.current_stance, 0) / agents.length
  const delta = agents.reduce((s, a) => s + (a.current_stance - a.initial_stance), 0) / agents.length

  return (
    <div className="glass-card p-4">
      <div className="text-xs font-semibold text-slate-400 mb-4">群体立场摘要</div>
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-xs text-slate-500">当前平均立场</span>
          <span className="font-mono font-bold text-sm" style={{ color: avg > 0 ? '#10b981' : '#f87171' }}>
            {avg > 0 ? '+' : ''}{avg.toFixed(3)}
          </span>
        </div>
        <div className="h-3 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
          <div className="h-full rounded-full" style={{
            width: `${((avg + 1) / 2) * 100}%`,
            background: avg > 0 ? 'linear-gradient(90deg, #94a3b8, #10b981)' : 'linear-gradient(90deg, #f87171, #94a3b8)',
          }} />
        </div>
        <div className="flex justify-between items-center">
          <span className="text-xs text-slate-500">仿真后立场漂移</span>
          <span className="font-mono text-xs flex items-center gap-1" style={{ color: delta > 0 ? '#10b981' : '#f87171' }}>
            {delta > 0 ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
            {delta > 0 ? '+' : ''}{delta.toFixed(3)}
          </span>
        </div>
      </div>
    </div>
  )
}

export default function ReportPage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [report, setReport] = useState('')
  const [agents, setAgents] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getReport(sessionId),
      getAgents(sessionId),
    ]).then(([r, a]) => {
      setReport(r.report)
      setAgents(a.agents)
    }).catch(console.error)
      .finally(() => setLoading(false))
  }, [sessionId])

  const handleDownload = () => {
    const blob = new Blob([report], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `goldto-report-${sessionId}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <FileText size={24} className="text-amber-400" />
          <h1 className="text-2xl font-bold text-white">预测报告</h1>
        </div>
        <div className="flex gap-3">
          <button onClick={handleDownload} className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm"
            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#e2e8f0' }}>
            <Download size={15} /> 下载报告
          </button>
          <button onClick={() => navigate(`/chat/${sessionId}`)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold"
            style={{ background: 'linear-gradient(135deg, #f59e0b, #d97706)', color: '#000' }}>
            <MessageCircle size={15} /> 与报告对话
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Report content */}
        <div className="col-span-2">
          <div className="glass-card p-6">
            {loading ? (
              <div className="flex items-center justify-center h-40 gap-3 text-slate-500">
                <div className="spinner w-5 h-5" /> 报告加载中...
              </div>
            ) : report ? (
              <MarkdownRenderer content={report} />
            ) : (
              <div className="text-slate-500 text-center py-12">报告尚未生成，请先完成仿真</div>
            )}
          </div>
        </div>

        {/* Sidebar analytics */}
        <div className="space-y-4">
          <StanceTimeline agents={agents} />
          <StanceChart agents={agents} />

          {/* Top agents */}
          <div className="glass-card p-4">
            <div className="text-xs font-semibold text-slate-400 mb-3">关键影响者</div>
            <div className="space-y-2">
              {[...agents]
                .sort((a, b) => Math.abs(b.current_stance) - Math.abs(a.current_stance))
                .slice(0, 5)
                .map(a => {
                  const color = a.current_stance > 0.2 ? '#10b981' : a.current_stance < -0.2 ? '#f87171' : '#94a3b8'
                  return (
                    <div key={a.id} className="flex items-center justify-between text-xs">
                      <div>
                        <div className="text-slate-300">{a.name}</div>
                        <div className="text-slate-600">{a.role}</div>
                      </div>
                      <span className="font-mono" style={{ color }}>
                        {a.current_stance > 0 ? '+' : ''}{a.current_stance.toFixed(2)}
                      </span>
                    </div>
                  )
                })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
