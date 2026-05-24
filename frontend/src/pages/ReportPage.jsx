import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { FileText, MessageCircle, Download, Radio, CheckCircle } from 'lucide-react'
import { getBriefing, getEvents } from '../api/client'

function MarkdownRenderer({ content }) {
  const lines = content.split('\n')
  const elements = []
  let i = 0

  const parseLine = str => {
    const parts = str.split(/\*\*(.*?)\*\*/g)
    return parts.map((p, idx) => idx % 2 === 1 ? <strong key={idx} style={{ color: '#fbbf24' }}>{p}</strong> : p)
  }

  while (i < lines.length) {
    const line = lines[i]

    if (line.startsWith('## ')) {
      elements.push(<h2 key={i} className="text-lg font-bold mt-6 mb-2" style={{ color: '#fbbf24' }}>{line.slice(3)}</h2>)
    } else if (line.startsWith('### ')) {
      elements.push(<h3 key={i} className="text-base font-semibold mt-4 mb-2 text-slate-200">{line.slice(4)}</h3>)
    } else if (line.startsWith('# ')) {
      elements.push(<h1 key={i} className="text-2xl font-bold mt-2 mb-3" style={{ color: '#fbbf24' }}>{line.slice(2)}</h1>)
    } else if (line.startsWith('| ') && line.endsWith(' |')) {
      // Simple table row handling
      const cells = line.split('|').slice(1, -1).map(c => c.trim())
      elements.push(
        <div key={i} className="grid gap-2 mb-1" style={{ gridTemplateColumns: `repeat(${cells.length}, 1fr)` }}>
          {cells.map((c, j) => (
            <div key={j} className={`text-xs p-2 rounded ${i > 0 && lines[i-1]?.startsWith('|---') ? 'text-slate-300' : 'text-slate-400'}`}
              style={{ background: 'rgba(255,255,255,0.03)' }}>
              {parseLine(c)}
            </div>
          ))}
        </div>
      )
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
    } else if (line.startsWith('---')) {
      elements.push(<hr key={i} className="my-4" style={{ borderColor: 'rgba(255,255,255,0.06)' }} />)
    } else {
      elements.push(<p key={i} className="text-slate-300 text-sm leading-relaxed mb-1">{parseLine(line)}</p>)
    }
    i++
  }
  return <div>{elements}</div>
}

export default function ReportPage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [briefing, setBriefing] = useState('')
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getBriefing(sessionId).catch(() => ({ briefing: '' })),
      getEvents(sessionId).catch(() => ({ events: [] })),
    ]).then(([b, e]) => {
      setBriefing(b.briefing)
      setEvents(e.events)
    }).catch(console.error)
      .finally(() => setLoading(false))
  }, [sessionId])

  const handleDownload = () => {
    const blob = new Blob([briefing], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `intelligence-briefing-${sessionId}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <FileText size={24} className="text-amber-400" />
          <h1 className="text-2xl font-bold text-white">情报简报</h1>
        </div>
        <div className="flex gap-3">
          <button onClick={handleDownload} className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm"
            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#e2e8f0' }}>
            <Download size={15} /> 下载简报
          </button>
          <button onClick={() => navigate(`/chat/${sessionId}`)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold"
            style={{ background: 'linear-gradient(135deg, #f59e0b, #d97706)', color: '#000' }}>
            <MessageCircle size={15} /> 深度对话
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Briefing content */}
        <div className="col-span-2">
          <div className="glass-card p-6">
            {loading ? (
              <div className="flex items-center justify-center h-40 gap-3 text-slate-500">
                <div className="spinner w-5 h-5" /> 简报加载中...
              </div>
            ) : briefing ? (
              <MarkdownRenderer content={briefing} />
            ) : (
              <div className="text-slate-500 text-center py-12">简报尚未生成，请先完成分析</div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Status */}
          <div className="glass-card p-4">
            <div className="text-xs font-semibold text-slate-400 mb-3 flex items-center gap-2">
              <CheckCircle size={12} /> 分析状态
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">数据源</span>
                <span className="text-amber-400">WorldMonitor</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Agent 团队</span>
                <span className="text-slate-300">CrewAI 4人组</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">事件数量</span>
                <span className="text-slate-300">{events.length} 条</span>
              </div>
            </div>
          </div>

          {/* Events summary */}
          <div className="glass-card p-4">
            <div className="text-xs font-semibold text-slate-400 mb-3 flex items-center gap-2">
              <Radio size={12} /> 关键事件
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {events.slice(0, 6).map((e, i) => (
                <div key={i} className="text-xs p-2 rounded" style={{ background: 'rgba(255,255,255,0.03)' }}>
                  <div className="text-slate-300 font-medium truncate">{e.title}</div>
                  <div className="text-slate-600 mt-0.5">{e.source} · {e.category}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
