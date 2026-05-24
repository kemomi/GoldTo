import React, { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar,
} from 'recharts'
import {
  BarChart3, FileText, Newspaper, Target, Calendar,
  TrendingUp, Globe, AlertCircle, ArrowRight, Zap,
  ExternalLink,
} from 'lucide-react'
import {
  getDashboardOverview,
  getDashboardTrends,
  getDashboardCategories,
  getDashboardSources,
  getHighRelevanceEvents,
} from '../api/dashboard'

/* ─── Constants ─── */

const CATEGORY_COLORS = {
  geopolitics: '#f87171',
  market: '#60a5fa',
  policy: '#c084fc',
  competitor: '#fb923c',
  social: '#f472b6',
  product: '#22d3ee',
  legal: '#facc15',
  tech: '#34d399',
  energy: '#fbbf24',
}

const CATEGORY_NAMES = {
  geopolitics: '地缘政治', market: '市场动态', policy: '政策监管',
  competitor: '竞争对手', social: '社交媒体', product: '产品趋势',
  legal: '法律合规', tech: '科技创新', energy: '能源',
}

const CHART_TEXT = { fill: '#94a3b8', fontSize: 11 }
const CHART_GRID = { stroke: 'rgba(255,255,255,0.05)' }

/* ─── Component ─── */

export default function DashboardPage() {
  const navigate = useNavigate()
  const [range, setRange] = useState(30)
  const [overview, setOverview] = useState(null)
  const [trends, setTrends] = useState([])
  const [categories, setCategories] = useState([])
  const [sources, setSources] = useState([])
  const [highRel, setHighRel] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)

  const hasData = useMemo(() => overview && overview.briefing_count > 0, [overview])

  useEffect(() => {
    setLoading(true)
    Promise.all([
      getDashboardOverview(),
      getDashboardTrends(range),
      getDashboardCategories(),
      getDashboardSources(),
      getHighRelevanceEvents({ limit: 10, min_relevance: 0.7 }),
    ])
      .then(([o, t, c, s, h]) => {
        if (o.success) setOverview(o.data)
        if (t.success) setTrends(t.data)
        if (c.success) setCategories(c.data)
        if (s.success) setSources(s.data)
        if (h.success) setHighRel(h.data)
        setLastUpdated(new Date())
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [range])

  if (loading) {
    return (
      <div className="min-h-full flex items-center justify-center">
        <div className="spinner w-6 h-6" />
      </div>
    )
  }

  return (
    <div className="min-h-full pb-12" style={{ background: 'var(--dark-900)' }}>
      {/* Header */}
      <div className="relative overflow-hidden" style={{
        background: 'linear-gradient(135deg, rgba(59,130,246,0.06) 0%, rgba(245,158,11,0.04) 100%)'
      }}>
        <div className="absolute inset-0 opacity-30" style={{
          backgroundImage: 'radial-gradient(circle at 80% 50%, rgba(59,130,246,0.12) 0%, transparent 50%)'
        }} />
        <div className="relative max-w-6xl mx-auto px-6 pt-8 pb-10">
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-2xl font-bold text-white mb-1">情报数据看板</h1>
              <p className="text-sm text-slate-400">
                洞察情报趋势，掌握战略先机
                {lastUpdated && (
                  <span className="ml-2 text-slate-600">
                    · 更新于 {lastUpdated.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                )}
              </p>
            </div>
            <RangeSelector value={range} onChange={setRange} />
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 -mt-4">
        {/* KPI Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <KpiCard
            icon={FileText}
            label="简报总数"
            value={overview?.briefing_count ?? 0}
            suffix="份"
            color="amber"
          />
          <KpiCard
            icon={Newspaper}
            label="情报事件"
            value={overview?.event_count ?? 0}
            suffix="条"
            color="blue"
          />
          <KpiCard
            icon={Target}
            label="平均相关度"
            value={overview?.avg_relevance ?? 0}
            suffix="%"
            color="emerald"
          />
          <KpiCard
            icon={Calendar}
            label="活跃监测天数"
            value={overview?.active_days ?? 0}
            suffix="天"
            color="purple"
          />
        </div>

        {!hasData ? (
          <EmptyState onGenerate={() => navigate('/briefings')} />
        ) : (
          <>
            {/* Charts Row 1 */}
            <div className="grid lg:grid-cols-3 gap-6 mb-6">
              {/* Trends */}
              <ChartCard title="情报趋势" icon={TrendingUp} className="lg:col-span-2">
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={trends} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="areaColor" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.15} />
                          <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid {...CHART_GRID} vertical={false} />
                      <XAxis
                        dataKey="date"
                        tickFormatter={d => d.slice(5)}
                        tick={CHART_TEXT}
                        axisLine={{ stroke: 'rgba(255,255,255,0.08)' }}
                        tickLine={false}
                      />
                      <YAxis
                        yAxisId="left"
                        tick={CHART_TEXT}
                        axisLine={false}
                        tickLine={false}
                        allowDecimals={false}
                      />
                      <YAxis
                        yAxisId="right"
                        orientation="right"
                        domain={[0, 100]}
                        tickFormatter={v => `${v}%`}
                        tick={CHART_TEXT}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip content={<DarkTooltip />} />
                      <Area
                        yAxisId="left"
                        type="monotone"
                        dataKey="event_count"
                        fill="url(#areaColor)"
                        stroke="#f59e0b"
                        strokeWidth={2}
                        dot={false}
                        activeDot={{ r: 4, fill: '#f59e0b', stroke: '#fff', strokeWidth: 2 }}
                      />
                      <Line
                        yAxisId="right"
                        type="monotone"
                        dataKey="avg_relevance"
                        stroke="#60a5fa"
                        strokeWidth={2}
                        dot={false}
                        activeDot={{ r: 4, fill: '#60a5fa', stroke: '#fff', strokeWidth: 2 }}
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
                {/* Legend */}
                <div className="flex items-center justify-center gap-6 mt-2">
                  <LegendItem color="#f59e0b" label="每日事件数" />
                  <LegendItem color="#60a5fa" label="平均相关度" dashed />
                </div>
              </ChartCard>

              {/* Categories */}
              <ChartCard title="类别分布" icon={BarChart3}>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={categories}
                        dataKey="count"
                        nameKey="category"
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={3}
                        stroke="none"
                      >
                        {categories.map((entry, i) => (
                          <Cell key={i} fill={CATEGORY_COLORS[entry.category] || '#94a3b8'} />
                        ))}
                      </Pie>
                      <Tooltip content={<PieTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex flex-wrap gap-2 justify-center mt-2">
                  {categories.map((c, i) => (
                    <span key={i} className="flex items-center gap-1 text-[11px] text-slate-400">
                      <span className="w-2 h-2 rounded-full" style={{ background: CATEGORY_COLORS[c.category] || '#94a3b8' }} />
                      {CATEGORY_NAMES[c.category] || c.category} ({c.count})
                    </span>
                  ))}
                </div>
              </ChartCard>
            </div>

            {/* Charts Row 2 */}
            <div className="grid lg:grid-cols-3 gap-6 mb-6">
              {/* Sources */}
              <ChartCard title="来源占比 Top 10" icon={Globe} className="lg:col-span-2">
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={sources}
                      layout="vertical"
                      margin={{ top: 10, right: 30, left: 20, bottom: 0 }}
                    >
                      <CartesianGrid {...CHART_GRID} horizontal={false} />
                      <XAxis type="number" tick={CHART_TEXT} axisLine={false} tickLine={false} allowDecimals={false} />
                      <YAxis
                        type="category"
                        dataKey="source"
                        tick={CHART_TEXT}
                        axisLine={false}
                        tickLine={false}
                        width={100}
                      />
                      <Tooltip content={<BarTooltip />} />
                      <Bar dataKey="count" radius={[0, 4, 4, 0]} fill="#3b82f6" barSize={20}>
                        {sources.map((_, i) => (
                          <Cell key={i} fill={`hsl(${210 + i * 15}, 70%, ${55 - i * 2}%)`} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>

              {/* High Relevance Events */}
              <ChartCard title="高相关性事件" icon={AlertCircle}>
                <div className="h-72 overflow-y-auto pr-1 custom-scrollbar">
                  <div className="space-y-3">
                    {highRel.map((ev, i) => (
                      <div
                        key={i}
                        className="p-3 rounded-xl cursor-pointer transition-all hover:bg-white/[0.04] group"
                        style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)' }}
                        onClick={() => ev.briefing_id && navigate(`/briefing/${ev.briefing_id}`)}
                      >
                        <div className="flex items-start justify-between gap-2 mb-1.5">
                          <h4 className="text-xs font-medium text-slate-200 leading-snug line-clamp-2 group-hover:text-amber-400 transition-colors flex-1 min-w-0">
                            {ev.title}
                          </h4>
                          <div className="flex items-center gap-1 shrink-0">
                            {ev.url && (
                              <a href={ev.url} target="_blank" rel="noopener noreferrer"
                                onClick={e => e.stopPropagation()}
                                className="p-1 rounded text-slate-600 hover:text-amber-400 hover:bg-amber-500/10 transition-all"
                                title="查看原始来源">
                                <ExternalLink size={10} />
                              </a>
                            )}
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 font-medium">
                              {(ev.relevance * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 text-[10px] text-slate-500">
                          <span>{ev.source}</span>
                          <span>·</span>
                          <span className="text-slate-400">{CATEGORY_NAMES[ev.category] || ev.category}</span>
                        </div>
                        {/* Relevance bar */}
                        <div className="mt-2 h-1 rounded-full bg-white/5 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-amber-500/60 to-amber-400"
                            style={{ width: `${ev.relevance * 100}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </ChartCard>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

/* ─── Sub-components ─── */

function RangeSelector({ value, onChange }) {
  const options = [
    { label: '7天', value: 7 },
    { label: '30天', value: 30 },
    { label: '全部', value: 365 },
  ]
  return (
    <div className="inline-flex items-center p-1 rounded-xl border border-white/5 bg-white/[0.02]">
      {options.map(opt => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            value === opt.value
              ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
              : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}

function KpiCard({ icon: Icon, label, value, suffix, color }) {
  const colorMap = {
    amber: 'from-amber-500/10 to-amber-500/5 border-amber-500/15 text-amber-400',
    blue: 'from-blue-500/10 to-blue-500/5 border-blue-500/15 text-blue-400',
    emerald: 'from-emerald-500/10 to-emerald-500/5 border-emerald-500/15 text-emerald-400',
    purple: 'from-purple-500/10 to-purple-500/5 border-purple-500/15 text-purple-400',
  }
  const cls = colorMap[color] || colorMap.amber
  return (
    <div className={`relative p-5 rounded-2xl border bg-gradient-to-br ${cls}`}>
      <div className="flex items-center gap-2 mb-3">
        <Icon size={14} />
        <span className="text-xs font-medium text-slate-400">{label}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-3xl font-bold text-white tracking-tight">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </span>
        <span className="text-sm text-slate-500">{suffix}</span>
      </div>
    </div>
  )
}

function ChartCard({ title, icon: Icon, children, className = '' }) {
  return (
    <div className={`p-5 rounded-2xl ${className}`} style={{
      background: 'var(--dark-800)',
      border: '1px solid rgba(255,255,255,0.06)'
    }}>
      <div className="flex items-center gap-2 mb-4">
        <div className="p-1 rounded-md bg-amber-500/10">
          <Icon size={13} className="text-amber-400" />
        </div>
        <h3 className="text-sm font-semibold text-white">{title}</h3>
      </div>
      {children}
    </div>
  )
}

function LegendItem({ color, label, dashed }) {
  return (
    <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
      <span className="w-3 h-0.5 rounded-full" style={{
        background: color,
        borderStyle: dashed ? 'dashed' : 'solid',
        borderWidth: dashed ? '1px 0 0 0' : '0',
        borderColor: color,
        height: dashed ? 0 : 3,
        marginTop: dashed ? 1 : 0,
      }} />
      {label}
    </div>
  )
}

function EmptyState({ onGenerate }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 rounded-2xl" style={{
      background: 'var(--dark-800)',
      border: '1px solid rgba(255,255,255,0.06)'
    }}>
      <div className="w-14 h-14 rounded-2xl bg-amber-500/5 flex items-center justify-center mb-4 border border-amber-500/10">
        <BarChart3 size={24} className="text-amber-400/50" />
      </div>
      <h3 className="text-base font-semibold text-white mb-1">暂无数据</h3>
      <p className="text-sm text-slate-500 mb-5">还没有生成过简报，数据看板需要至少一份简报才能展示趋势。</p>
      <button
        onClick={onGenerate}
        className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 text-sm font-medium hover:bg-amber-500/20 transition-colors"
      >
        <Zap size={14} />
        前往生成简报
      </button>
    </div>
  )
}

/* ─── Recharts Custom Tooltips ─── */

function DarkTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg px-3 py-2 text-xs border"
      style={{ background: 'rgba(17,17,24,0.95)', borderColor: 'rgba(255,255,255,0.1)' }}>
      <div className="text-slate-300 font-medium mb-1">{label}</div>
      {payload.map((p, i) => (
        <div key={i} className="flex items-center gap-2 text-slate-400">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span>{p.name}:</span>
          <span className="text-white font-medium">
            {p.dataKey === 'avg_relevance' ? `${p.value}%` : p.value}
          </span>
        </div>
      ))}
    </div>
  )
}

function PieTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const p = payload[0]
  const cat = p?.payload?.category
  const name = CATEGORY_NAMES[cat] || cat
  return (
    <div className="rounded-lg px-3 py-2 text-xs border"
      style={{ background: 'rgba(17,17,24,0.95)', borderColor: 'rgba(255,255,255,0.1)' }}>
      <div className="flex items-center gap-2 text-slate-300 font-medium">
        <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
        {name}
      </div>
      <div className="text-slate-400 mt-1">
        数量: <span className="text-white">{p.value}</span>
        <span className="mx-1">·</span>
        占比: <span className="text-white">{p?.payload?.percent ? (p.payload.percent * 100).toFixed(1) : 0}%</span>
      </div>
    </div>
  )
}

function BarTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg px-3 py-2 text-xs border"
      style={{ background: 'rgba(17,17,24,0.95)', borderColor: 'rgba(255,255,255,0.1)' }}>
      <span className="text-slate-400">{payload[0].payload.source}: </span>
      <span className="text-white font-medium">{payload[0].value} 条</span>
    </div>
  )
}
