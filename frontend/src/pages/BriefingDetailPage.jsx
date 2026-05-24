import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ChevronLeft, Calendar, FileText, Globe, Shield,
  AlertTriangle, TrendingUp, Zap, ArrowUpRight,
  ExternalLink, Clock, BarChart3, Sparkles, Target,
  Newspaper, Link2
} from 'lucide-react'
import { getBriefing } from '../api/briefing'

/* ─── Helpers ─── */

/** Strip HTML tags, keep text. Also decode common entities. */
function stripHtml(html) {
  if (!html) return ''
  const tmp = document.createElement('div')
  tmp.innerHTML = html
    .replace(/<p\b[^>]*>/gi, '\n')
    .replace(/<\/p\b[^>]*>/gi, '\n')
    .replace(/<br\b[^>]*\/?>/gi, '\n')
    .replace(/<img\b[^>]*\/?>/gi, ' [图片] ')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
  const text = tmp.textContent || tmp.innerText || ''
  return text.replace(/\n{3,}/g, '\n\n').trim()
}

/** Parse risk level string into color + icon */
function parseRiskLevel(text) {
  const t = (text || '').toLowerCase()
  if (t.includes('高') || t.includes('red') || t.includes('🔴')) {
    return { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20', dot: 'bg-red-400', label: '高风险' }
  }
  if (t.includes('中') || t.includes('yellow') || t.includes('🟡') || t.includes('orange')) {
    return { color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20', dot: 'bg-amber-400', label: '中风险' }
  }
  if (t.includes('低') || t.includes('green') || t.includes('🟢')) {
    return { color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', dot: 'bg-emerald-400', label: '低风险' }
  }
  return { color: 'text-slate-400', bg: 'bg-slate-500/10', border: 'border-slate-500/20', dot: 'bg-slate-400', label: '未知' }
}

const categoryConfig = {
  geopolitics: { name: '地缘政治', color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20', dot: 'bg-red-400', icon: Globe },
  market:      { name: '市场动态', color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20', dot: 'bg-blue-400', icon: BarChart3 },
  policy:      { name: '政策监管', color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20', dot: 'bg-purple-400', icon: Shield },
  competitor:  { name: '竞争对手', color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/20', dot: 'bg-orange-400', icon: Target },
  social:      { name: '社交媒体', color: 'text-pink-400', bg: 'bg-pink-500/10', border: 'border-pink-500/20', dot: 'bg-pink-400', icon: Sparkles },
  product:     { name: '产品趋势', color: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/20', dot: 'bg-cyan-400', icon: Zap },
  legal:       { name: '法律合规', color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20', dot: 'bg-yellow-400', icon: Shield },
  tech:        { name: '科技创新', color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', dot: 'bg-emerald-400', icon: Zap },
  energy:      { name: '能源',     color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20', dot: 'bg-amber-400', icon: Zap },
}

/* ─── Component ─── */

export default function BriefingDetailPage() {
  const { briefingId } = useParams()
  const navigate = useNavigate()
  const [briefing, setBriefing] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getBriefing(briefingId)
      .then(data => setBriefing(data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [briefingId])

  if (loading) {
    return (
      <div className="min-h-full flex items-center justify-center">
        <div className="spinner w-6 h-6" />
      </div>
    )
  }
  if (!briefing) {
    return (
      <div className="min-h-full flex items-center justify-center text-slate-500">
        简报不存在或已被删除
      </div>
    )
  }

  const events = briefing.events || []
  const uniqueCategories = [...new Set(events.map(e => e.category).filter(Boolean))]
  const hasRisk = briefing.risk_assessment && Object.keys(briefing.risk_assessment).length > 0
  const hasRecs = briefing.recommendations && briefing.recommendations.length > 0

  return (
    <div className="min-h-full pb-16" style={{ background: 'var(--dark-900)' }}>
      {/* ═══════════ 顶部 Hero 区域 ═══════════ */}
      <div className="relative overflow-hidden" style={{ background: 'linear-gradient(135deg, rgba(245,158,11,0.08) 0%, rgba(59,130,246,0.04) 100%)' }}>
        <div className="absolute inset-0 opacity-30" style={{
          backgroundImage: 'radial-gradient(circle at 20% 50%, rgba(245,158,11,0.15) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(59,130,246,0.1) 0%, transparent 50%)'
        }} />

        <div className="relative max-w-4xl mx-auto px-6 pt-8 pb-10">
          {/* 返回按钮 */}
          <button
            onClick={() => navigate(-1)}
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors mb-6"
          >
            <ChevronLeft size={14} />
            返回简报列表
          </button>

          {/* 日期徽章 + 标题 */}
          <div className="flex items-start gap-4 mb-6">
            <div className="shrink-0 flex flex-col items-center px-3 py-2 rounded-xl border border-amber-500/20 bg-amber-500/5">
              <span className="text-[10px] uppercase tracking-wider text-amber-400/70 font-medium">
                {briefing.date ? new Date(briefing.date).toLocaleString('zh-CN', { month: 'short' }) : ''}
              </span>
              <span className="text-2xl font-bold text-amber-400 leading-none mt-0.5">
                {briefing.date ? new Date(briefing.date).getDate() : ''}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <h1 className="text-2xl font-bold text-white leading-tight mb-2">
                {briefing.title || '每日战略简报'}
              </h1>
              <p className="text-sm text-slate-400">
                {briefing.date} · 由 GoldTo Intelligence Engine 自动生成
              </p>
            </div>
          </div>

          {/* 统计微卡片 */}
          <div className="flex flex-wrap gap-3">
            <StatBadge icon={FileText} value={events.length} label="条情报" />
            <StatBadge icon={Globe} value={briefing.sources_count || 0} label="个来源" />
            <StatBadge icon={Target} value={uniqueCategories.length} label="个维度" />
            <StatBadge icon={Clock} value="每日" label="更新频率" />
          </div>
        </div>
      </div>

      {/* ═══════════ 主体内容 ═══════════ */}
      <div className="max-w-4xl mx-auto px-6 -mt-4">

        {/* ── 核心摘要 ── */}
        {briefing.summary && (
          <section className="mb-8">
            <div className="relative p-5 rounded-2xl border-l-4 border-amber-400"
              style={{ background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.12)', borderLeftWidth: '4px' }}>
              <div className="flex items-center gap-2 mb-3">
                <div className="p-1.5 rounded-lg bg-amber-500/10">
                  <Sparkles size={14} className="text-amber-400" />
                </div>
                <span className="text-sm font-semibold text-amber-400">核心摘要</span>
              </div>
              <p className="text-sm text-slate-200 leading-relaxed">
                {stripHtml(briefing.summary)}
              </p>
            </div>
          </section>
        )}

        {/* ── 风险评估 + 决策建议 ── */}
        {(hasRisk || hasRecs) && (
          <section className="mb-8">
            <SectionHeader icon={AlertTriangle} title="研判与建议" />
            <div className="grid md:grid-cols-2 gap-4">
              {hasRisk && (
                <div className="p-5 rounded-2xl" style={{ background: 'var(--dark-800)', border: '1px solid rgba(255,255,255,0.06)' }}>
                  <div className="flex items-center gap-2 mb-4">
                    <div className="p-1 rounded-md bg-red-500/10">
                      <AlertTriangle size={13} className="text-red-400" />
                    </div>
                    <span className="text-sm font-semibold text-red-400">风险评估</span>
                  </div>
                  <div className="space-y-3">
                    {Object.entries(briefing.risk_assessment).map(([key, val]) => {
                      const risk = parseRiskLevel(String(val))
                      return (
                        <div key={key} className="flex items-center justify-between">
                          <span className="text-sm text-slate-400">{key}</span>
                          <div className="flex items-center gap-2">
                            <span className={`w-2 h-2 rounded-full ${risk.dot}`} />
                            <span className={`text-sm font-medium ${risk.color}`}>{val}</span>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {hasRecs && (
                <div className="p-5 rounded-2xl" style={{ background: 'var(--dark-800)', border: '1px solid rgba(255,255,255,0.06)' }}>
                  <div className="flex items-center gap-2 mb-4">
                    <div className="p-1 rounded-md bg-emerald-500/10">
                      <TrendingUp size={13} className="text-emerald-400" />
                    </div>
                    <span className="text-sm font-semibold text-emerald-400">决策建议</span>
                  </div>
                  <div className="space-y-3">
                    {briefing.recommendations.map((rec, i) => (
                      <div key={i} className="flex items-start gap-3">
                        <span className="shrink-0 w-5 h-5 rounded-full bg-emerald-500/10 text-emerald-400 text-[10px] font-bold flex items-center justify-center mt-0.5">
                          {i + 1}
                        </span>
                        <p className="text-sm text-slate-300 leading-relaxed">{rec}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </section>
        )}

        {/* ── 关键情报事件（时间线） ── */}
        {events.length > 0 && (
          <section className="mb-8">
            <SectionHeader icon={Newspaper} title={`关键情报事件 · ${events.length} 条`} />

            <div className="relative">
              {/* 时间线竖线 */}
              <div className="absolute left-3.5 top-3 bottom-3 w-px bg-gradient-to-b from-slate-600/40 via-slate-600/20 to-transparent" />

              <div className="space-y-4">
                {events.map((ev, i) => {
                  const cfg = categoryConfig[ev.category] || categoryConfig.market
                  const Icon = cfg.icon
                  const cleanSummary = stripHtml(ev.summary)
                  const timeLabel = ev.timestamp
                    ? new Date(ev.timestamp).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
                    : ''

                  return (
                    <div key={i} className="relative pl-10">
                      {/* 时间线圆点 */}
                      <div className={`absolute left-2 top-3.5 w-3 h-3 rounded-full border-2 border-[var(--dark-900)] ${cfg.dot}`} />

                      {/* 事件卡片 */}
                      <div className="p-4 rounded-xl transition-all hover:bg-white/[0.02]"
                        style={{ background: 'var(--dark-800)', border: '1px solid rgba(255,255,255,0.05)' }}>

                        {/* 卡片头部：类别标签 + 标题 */}
                        <div className="flex items-start gap-3 mb-2.5">
                          <span className={`shrink-0 inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full border ${cfg.bg} ${cfg.color} ${cfg.border} font-medium`}>
                            <Icon size={10} />
                            {cfg.name}
                          </span>
                          {ev.url ? (
                            <a href={ev.url} target="_blank" rel="noopener noreferrer"
                              className="text-sm font-semibold text-white leading-snug flex-1 min-w-0 hover:text-amber-400 transition-colors group/link">
                              {stripHtml(ev.title)}
                              <ExternalLink size={11} className="inline-block ml-1 text-slate-500 group-hover/link:text-amber-400 transition-colors" />
                            </a>
                          ) : (
                            <h3 className="text-sm font-semibold text-white leading-snug flex-1 min-w-0">
                              {stripHtml(ev.title)}
                            </h3>
                          )}
                        </div>

                        {/* 摘要 */}
                        {cleanSummary && (
                          <p className="text-[13px] text-slate-400 leading-relaxed mb-3 pl-0.5">
                            {cleanSummary}
                          </p>
                        )}

                        {/* 元数据行 */}
                        <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-500 mb-3">
                          <span className="flex items-center gap-1">
                            <Globe size={10} />
                            {ev.source}
                          </span>
                          {timeLabel && (
                            <span className="flex items-center gap-1">
                              <Clock size={10} />
                              {timeLabel}
                            </span>
                          )}
                          <span className="flex items-center gap-1">
                            <Target size={10} />
                            相关度 <span className="text-slate-300 font-medium">{(ev.relevance * 100).toFixed(0)}%</span>
                          </span>
                          {ev.url && (
                            <a href={ev.url} target="_blank" rel="noopener noreferrer"
                              className="flex items-center gap-1 text-amber-400/70 hover:text-amber-400 transition-colors ml-auto">
                              <ExternalLink size={10} />
                              阅读原文
                            </a>
                          )}
                        </div>

                        {/* 来源参考 */}
                        {ev.sources_reference && ev.sources_reference.length > 0 && (
                          <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-white/5">
                            <span className="flex items-center gap-1 text-[11px] text-slate-500">
                              <Link2 size={10} />
                              来源参考
                            </span>
                            {ev.sources_reference.slice(0, 4).map((ref, ri) => (
                              <a key={ri} href={ref.url} target="_blank" rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-md bg-white/[0.03] text-slate-300 hover:bg-white/[0.06] hover:text-white border border-white/[0.06] transition-all"
                                title={ref.desc}>
                                {ref.name}
                                <ArrowUpRight size={9} className="opacity-50" />
                              </a>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </section>
        )}

        {/* ── 完整简报 Markdown ── */}
        {briefing.full_content && (
          <section className="mb-8">
            <SectionHeader icon={FileText} title="完整简报" />
            <div className="p-6 rounded-2xl" style={{ background: 'var(--dark-800)', border: '1px solid rgba(255,255,255,0.06)' }}>
              <MarkdownContent content={briefing.full_content} />
            </div>
          </section>
        )}
      </div>
    </div>
  )
}

/* ─── Sub-components ─── */

function StatBadge({ icon: Icon, value, label }) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-xl border border-white/5 bg-white/[0.02]">
      <Icon size={13} className="text-slate-400" />
      <span className="text-sm font-bold text-white">{value}</span>
      <span className="text-[11px] text-slate-500">{label}</span>
    </div>
  )
}

function SectionHeader({ icon: Icon, title }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <div className="p-1.5 rounded-lg bg-amber-500/10">
        <Icon size={14} className="text-amber-400" />
      </div>
      <h2 className="text-base font-bold text-white">{title}</h2>
      <div className="flex-1 h-px bg-gradient-to-r from-white/10 to-transparent ml-2" />
    </div>
  )
}

/* ─── Markdown Renderer (with HTML stripping) ─── */

function MarkdownContent({ content }) {
  // First strip HTML tags from raw content
  const cleaned = stripHtml(content)
  const lines = cleaned.split('\n')
  const elements = []
  let i = 0

  while (i < lines.length) {
    const line = lines[i]

    // Code block
    if (line.startsWith('```')) {
      const codeLines = []
      i++
      while (i < lines.length && !lines[i].startsWith('```')) {
        codeLines.push(lines[i])
        i++
      }
      i++
      elements.push(
        <pre key={i} className="bg-black/30 rounded-lg p-3 my-3 overflow-x-auto text-xs font-mono text-slate-300 border border-white/5">
          {codeLines.join('\n')}
        </pre>
      )
      continue
    }

    // Table
    if (line.startsWith('|') && i + 1 < lines.length && lines[i + 1].startsWith('|')) {
      const tableLines = []
      while (i < lines.length && lines[i].startsWith('|')) {
        tableLines.push(lines[i])
        i++
      }
      elements.push(<MarkdownTable key={i} lines={tableLines} />)
      continue
    }

    // Numbered list (e.g. "1. **Short-term**: ...")
    const numMatch = line.match(/^(\d+)\.\s+(.*)/)
    if (numMatch && !line.startsWith('#')) {
      elements.push(
        <div key={i} className="flex items-start gap-3 my-2">
          <span className="shrink-0 w-5 h-5 rounded-full bg-amber-500/10 text-amber-400 text-[10px] font-bold flex items-center justify-center mt-0.5">
            {numMatch[1]}
          </span>
          <span className="text-sm text-slate-300 leading-relaxed">{renderInline(numMatch[2])}</span>
        </div>
      )
      i++
      continue
    }

    // Headings
    if (line.startsWith('# ')) {
      elements.push(<h1 key={i} className="text-xl font-bold text-amber-400 mt-8 mb-3">{renderInline(line.slice(2))}</h1>)
    } else if (line.startsWith('## ')) {
      elements.push(<h2 key={i} className="text-lg font-bold text-amber-400 mt-6 mb-3">{renderInline(line.slice(3))}</h2>)
    } else if (line.startsWith('### ')) {
      elements.push(<h3 key={i} className="text-sm font-bold text-amber-400/80 mt-5 mb-2 uppercase tracking-wider">{renderInline(line.slice(4))}</h3>)
    } else if (line.startsWith('> ')) {
      elements.push(
        <blockquote key={i} className="border-l-2 border-amber-500/30 pl-4 my-3 text-sm text-slate-400 italic bg-amber-500/[0.03] py-2 pr-3 rounded-r-lg">
          {renderInline(line.slice(2))}
        </blockquote>
      )
    } else if (line.startsWith('- ') || line.startsWith('* ')) {
      elements.push(
        <li key={i} className="text-sm text-slate-300 ml-2 mb-1.5 flex items-start gap-2 leading-relaxed">
          <span className="text-amber-400 mt-1.5">•</span>
          <span>{renderInline(line.slice(2))}</span>
        </li>
      )
    } else if (line.trim() === '') {
      elements.push(<div key={i} className="h-1" />)
    } else if (line.trim() === '---') {
      elements.push(<hr key={i} className="border-white/10 my-5" />)
    } else {
      elements.push(<p key={i} className="text-sm text-slate-300 leading-relaxed mb-2">{renderInline(line)}</p>)
    }
    i++
  }

  return <div>{elements}</div>
}

function renderInline(text) {
  const parts = []
  let remaining = text
  let key = 0

  while (remaining.length > 0) {
    const linkMatch = remaining.match(/\[([^\]]+)\]\(([^\)]+)\)/)
    const boldMatch = remaining.match(/\*\*(.+?)\*\*/)
    const codeMatch = remaining.match(/`([^`]+)`/)

    const linkIdx = linkMatch ? linkMatch.index : Infinity
    const boldIdx = boldMatch ? boldMatch.index : Infinity
    const codeIdx = codeMatch ? codeMatch.index : Infinity

    const firstIdx = Math.min(linkIdx, boldIdx, codeIdx)

    if (firstIdx === Infinity) {
      parts.push(<span key={key++}>{remaining}</span>)
      break
    }

    if (firstIdx > 0) {
      parts.push(<span key={key++}>{remaining.slice(0, firstIdx)}</span>)
    }

    if (firstIdx === linkIdx && linkMatch) {
      parts.push(
        <a key={key++} href={linkMatch[2]} target="_blank" rel="noopener noreferrer"
          className="text-amber-400 hover:text-amber-300 underline underline-offset-2">
          {linkMatch[1]}
        </a>
      )
      remaining = remaining.slice(linkIdx + linkMatch[0].length)
    } else if (firstIdx === boldIdx && boldMatch) {
      parts.push(<strong key={key++} className="text-amber-400 font-semibold">{boldMatch[1]}</strong>)
      remaining = remaining.slice(boldIdx + boldMatch[0].length)
    } else if (firstIdx === codeIdx && codeMatch) {
      parts.push(<code key={key++} className="bg-amber-500/10 text-amber-300 px-1 py-0.5 rounded text-xs font-mono">{codeMatch[1]}</code>)
      remaining = remaining.slice(codeIdx + codeMatch[0].length)
    } else {
      parts.push(<span key={key++}>{remaining}</span>)
      break
    }
  }

  return parts.length === 1 ? parts[0] : <>{parts}</>
}

function MarkdownTable({ lines }) {
  const dataLines = lines.filter(l => !l.replace(/\|/g, '').trim().match(/^[-:]+$/))
  if (dataLines.length === 0) return null

  const rows = dataLines.map(line =>
    line.split('|').map(c => c.trim()).filter(c => c !== '')
  )
  if (rows.length === 0) return null

  return (
    <div className="overflow-x-auto my-4">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="border-b border-amber-500/20">
            {rows[0].map((cell, j) => (
              <th key={j} className="text-left py-2.5 px-3 text-amber-400 font-medium">{cell}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(1).map((row, ri) => (
            <tr key={ri} className="border-b border-white/5">
              {row.map((cell, ci) => (
                <td key={ci} className="py-2.5 px-3 text-slate-300">{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
