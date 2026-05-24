import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search, Zap, ArrowRight, FileText, AlertCircle, Radio,
  BarChart3, Newspaper, Bell, Settings, TrendingUp, Calendar,
  Target, Clock, CheckCircle, XCircle, Send, Eye, RefreshCw,
  Shield, ChevronRight, Activity, Globe,
} from 'lucide-react'
import { createSession, collectData, uploadSeed } from '../api/client'
import { getDashboardOverview } from '../api/dashboard'
import { getTodayBriefingStatus, generateBriefingNow } from '../api/briefing'
import { listAlerts } from '../api/alert'

const EXAMPLES = [
  { icon: '🌍', label: '地缘政治', topic: '中东局势升级对全球能源市场的影响' },
  { icon: '📈', label: '金融市场', topic: '美联储降息预期下的科技股走势分析' },
  { icon: '🏛️', label: '政策监管', topic: '欧盟AI法案对全球科技产业的影响' },
  { icon: '⚡', label: '能源转型', topic: '锂价波动对新能源汽车供应链的影响' },
]

const CATEGORY_NAMES = {
  geopolitics: '地缘政治', market: '市场动态', policy: '政策监管',
  competitor: '竞争对手', social: '社交媒体', product: '产品趋势',
  legal: '法律合规', tech: '科技创新', energy: '能源',
}

export default function HomePage() {
  const navigate = useNavigate()
  const fileRef = useRef()

  // ── CrewAI state ──
  const [topic, setTopic] = useState('')
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // ── Dashboard state ──
  const [overview, setOverview] = useState(null)
  const [todayStatus, setTodayStatus] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [pageLoading, setPageLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [pollTimer, setPollTimer] = useState(null)

  const fetchDashboard = async () => {
    try {
      const [o, t, a] = await Promise.all([
        getDashboardOverview(),
        getTodayBriefingStatus(),
        listAlerts({ limit: 5 }),
      ])
      if (o.success) setOverview(o.data)
      setTodayStatus(t)
      if (a.success) setAlerts(a.alerts || [])
    } catch (e) {
      console.error(e)
    } finally {
      setPageLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboard()
    return () => {
      if (pollTimer) clearInterval(pollTimer)
    }
  }, [])

  // Poll when generating
  useEffect(() => {
    if (todayStatus?.status === 'generating') {
      const timer = setInterval(async () => {
        try {
          const res = await getTodayBriefingStatus()
          setTodayStatus(res)
          if (res.status !== 'generating') {
            clearInterval(timer)
            fetchDashboard()
          }
        } catch (e) {
          console.error(e)
        }
      }, 3000)
      setPollTimer(timer)
      return () => clearInterval(timer)
    }
  }, [todayStatus?.status])

  // ── CrewAI handlers ──
  const handleDrop = e => {
    e.preventDefault()
    const f = e.dataTransfer.files[0]
    if (f) setFile(f)
  }

  const handleSubmit = async () => {
    if (!topic.trim()) return setError('请输入分析主题')
    setError('')
    setLoading(true)
    try {
      const { session_id } = await createSession()
      if (file) {
        const fd = new FormData()
        fd.append('file', file)
        fd.append('prediction_goal', topic)
        await uploadSeed(session_id, fd)
      }
      await collectData(session_id, topic)
      navigate(`/simulate/${session_id}`)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
      setLoading(false)
    }
  }

  const handleGenerateBriefing = async () => {
    setGenerating(true)
    try {
      await generateBriefingNow()
      setTodayStatus(prev => prev ? { ...prev, status: 'generating' } : { date: '', status: 'generating' })
    } catch (e) {
      console.error(e)
      setGenerating(false)
    }
  }

  const statusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle size={14} className="text-green-400" />
      case 'generating': return <Clock size={14} className="text-amber-400 animate-pulse" />
      case 'failed': return <XCircle size={14} className="text-red-400" />
      case 'sent': return <Send size={14} className="text-blue-400" />
      default: return <AlertCircle size={14} className="text-slate-500" />
    }
  }

  const statusText = (status) => {
    const map = { completed: '已完成', generating: '生成中', draft: '草稿', failed: '失败', sent: '已推送', not_started: '未开始' }
    return map[status] || status
  }

  const today = new Date()
  const greeting = today.getHours() < 12 ? '早安' : today.getHours() < 18 ? '下午好' : '晚上好'

  return (
    <div className="min-h-full pb-12" style={{ background: 'var(--dark-900)' }}>
      {/* ═══════ 顶部欢迎栏 ═══════ */}
      <div className="relative overflow-hidden" style={{
        background: 'linear-gradient(135deg, rgba(245,158,11,0.06) 0%, rgba(59,130,246,0.03) 100%)'
      }}>
        <div className="absolute inset-0 opacity-30" style={{
          backgroundImage: 'radial-gradient(circle at 20% 50%, rgba(245,158,11,0.1) 0%, transparent 50%)'
        }} />
        <div className="relative max-w-6xl mx-auto px-6 pt-8 pb-6">
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-xl font-bold text-white mb-1">{greeting}，欢迎回到 GoldTo 情报中心</h1>
              <p className="text-sm text-slate-500">
                {today.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={fetchDashboard}
                className="p-2 rounded-xl border border-white/5 bg-white/[0.02] text-slate-500 hover:text-white transition-all"
              >
                <RefreshCw size={14} />
              </button>
              <span className="text-[11px] px-2.5 py-1.5 rounded-lg border border-amber-500/20 bg-amber-500/5 text-amber-400/80">
                Mock 模式
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 -mt-3">
        {/* ═══════ KPI Cards ═══════ */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <KpiCard icon={Newspaper} label="简报总数" value={overview?.briefing_count ?? 0} suffix="份" color="amber" loading={pageLoading} />
          <KpiCard icon={FileText} label="情报事件" value={overview?.event_count ?? 0} suffix="条" color="blue" loading={pageLoading} />
          <KpiCard icon={Target} label="平均相关度" value={overview?.avg_relevance ?? 0} suffix="%" color="emerald" loading={pageLoading} />
          <KpiCard icon={Calendar} label="活跃监测天数" value={overview?.active_days ?? 0} suffix="天" color="purple" loading={pageLoading} />
        </div>

        {/* ═══════ Row 2: Briefing Status + Alerts ═══════ */}
        <div className="grid lg:grid-cols-2 gap-6 mb-6">
          {/* Today Briefing */}
          <div className="p-5 rounded-2xl" style={{ background: 'var(--dark-800)', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-amber-500/10">
                  <Activity size={14} className="text-amber-400" />
                </div>
                <h3 className="text-sm font-semibold text-white">今日简报</h3>
              </div>
              {todayStatus?.status && (
                <div className="flex items-center gap-1.5 text-xs">
                  {statusIcon(todayStatus.status)}
                  <span className="text-slate-400">{statusText(todayStatus.status)}</span>
                </div>
              )}
            </div>

            {pageLoading ? (
              <SkeletonBlock />
            ) : !todayStatus || todayStatus.status === 'not_started' ? (
              <div className="text-center py-6">
                <div className="text-sm text-slate-500 mb-3">今日简报尚未生成</div>
                <button
                  onClick={handleGenerateBriefing}
                  disabled={generating}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 hover:bg-amber-500/20 transition-all disabled:opacity-50"
                >
                  <Zap size={12} />
                  {generating ? '生成中...' : '立即生成今日简报'}
                </button>
              </div>
            ) : (
              <div>
                <div className="text-lg font-bold text-white mb-1">
                  {todayStatus.date} 每日战略简报
                </div>
                <div className="flex items-center gap-4 text-xs text-slate-500 mb-4">
                  <span>{todayStatus.events_count || 0} 条情报</span>
                  <span>·</span>
                  <span>{todayStatus.briefing_id || '--'}</span>
                </div>
                <div className="flex items-center gap-2">
                  {todayStatus.status === 'completed' && todayStatus.briefing_id && (
                    <button
                      onClick={() => navigate(`/briefing/${todayStatus.briefing_id}`)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-amber-500/30 text-amber-400 hover:bg-amber-500/10 transition-all"
                    >
                      <Eye size={12} /> 查看简报
                    </button>
                  )}
                  {todayStatus.status === 'generating' && (
                    <span className="text-xs text-amber-400 animate-pulse">正在生成中，请稍候...</span>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Recent Alerts */}
          <div className="p-5 rounded-2xl" style={{ background: 'var(--dark-800)', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-red-500/10">
                  <Bell size={14} className="text-red-400" />
                </div>
                <h3 className="text-sm font-semibold text-white">最近告警</h3>
              </div>
              <button
                onClick={() => navigate('/alerts')}
                className="text-[11px] text-slate-500 hover:text-amber-400 transition-colors flex items-center gap-1"
              >
                查看全部 <ChevronRight size={10} />
              </button>
            </div>

            {pageLoading ? (
              <SkeletonBlock />
            ) : alerts.length === 0 ? (
              <div className="text-center py-6">
                <div className="w-10 h-10 rounded-xl bg-green-500/5 flex items-center justify-center mx-auto mb-2 border border-green-500/10">
                  <Shield size={16} className="text-green-400/40" />
                </div>
                <div className="text-xs text-slate-500">暂无告警，系统安静运行中</div>
              </div>
            ) : (
              <div className="space-y-2.5">
                {alerts.slice(0, 5).map((alert, i) => (
                  <div key={i} className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-white/[0.02] transition-colors cursor-pointer"
                    onClick={() => navigate('/alerts')}>
                    <span className={`shrink-0 w-1.5 h-1.5 rounded-full ${
                      alert.matched_reason === 'relevance' ? 'bg-amber-400' : 'bg-blue-400'
                    }`} />
                    <div className="flex-1 min-w-0">
                      <div className="text-xs text-slate-300 truncate">{alert.event_title}</div>
                      <div className="text-[10px] text-slate-500 mt-0.5">
                        {CATEGORY_NAMES[alert.event_category] || alert.event_category} · 相关度 {(alert.event_relevance * 100).toFixed(0)}%
                      </div>
                    </div>
                    <span className="text-[10px] text-slate-600">
                      {alert.triggered_at ? new Date(alert.triggered_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : ''}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ═══════ Quick Nav ═══════ */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <NavCard icon={BarChart3} title="数据看板" desc="情报趋势与可视化分析" color="blue" onClick={() => navigate('/dashboard')} />
          <NavCard icon={Newspaper} title="简报历史" desc="查看全部历史简报记录" color="amber" onClick={() => navigate('/briefings')} />
          <NavCard icon={Bell} title="情报预警" desc="实时告警与推送记录" color="red" onClick={() => navigate('/alerts')} badge={alerts.length > 0 ? alerts.length : null} />
          <NavCard icon={Settings} title="系统配置" desc="推送渠道与预警规则" color="slate" onClick={() => navigate('/settings')} />
        </div>

        {/* ═══════ CrewAI Analysis Entry ═══════ */}
        <div className="flex justify-center mb-8">
          <div className="w-full max-w-2xl rounded-2xl p-6" style={{ background: 'var(--dark-800)', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div className="flex items-center gap-2 mb-4">
              <div className="p-1.5 rounded-lg bg-purple-500/10">
                <Zap size={14} className="text-purple-400" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">高级情报分析</h3>
                <p className="text-[11px] text-slate-500">CrewAI 多 Agent 协同深度分析</p>
              </div>
            </div>

            <div className="mb-4">
              <textarea
                className="w-full rounded-xl px-4 py-3 text-sm resize-none outline-none transition-all"
                style={{
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  color: 'var(--text-primary)',
                  minHeight: 64,
                }}
                placeholder="例如：中东局势升级对全球能源市场的影响"
                value={topic}
                onChange={e => setTopic(e.target.value)}
                onFocus={e => e.target.style.borderColor = 'rgba(245,158,11,0.4)'}
                onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.08)'}
              />
              <div className="flex flex-wrap gap-2 mt-2">
                {EXAMPLES.map(ex => (
                  <button
                    key={ex.label}
                    onClick={() => setTopic(ex.topic)}
                    className="text-xs px-3 py-1 rounded-full border transition-all"
                    style={{ borderColor: 'rgba(255,255,255,0.1)', color: 'var(--text-secondary)' }}
                    onMouseEnter={e => { e.target.style.borderColor = 'rgba(245,158,11,0.4)'; e.target.style.color = '#fbbf24' }}
                    onMouseLeave={e => { e.target.style.borderColor = 'rgba(255,255,255,0.1)'; e.target.style.color = 'var(--text-secondary)' }}
                  >
                    {ex.icon} {ex.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="mb-4">
              <div
                className="border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-all"
                style={{ borderColor: file ? 'rgba(245,158,11,0.5)' : 'rgba(255,255,255,0.1)', background: file ? 'rgba(245,158,11,0.03)' : 'transparent' }}
                onDrop={handleDrop}
                onDragOver={e => e.preventDefault()}
                onClick={() => fileRef.current?.click()}
              >
                <input ref={fileRef} type="file" accept=".txt,.pdf,.md" className="hidden" onChange={e => setFile(e.target.files[0])} />
                {file ? (
                  <div className="flex items-center justify-center gap-2">
                    <FileText size={16} className="text-amber-400" />
                    <div className="text-sm text-white">{file.name}</div>
                    <div className="text-xs text-slate-500">({(file.size / 1024).toFixed(1)} KB)</div>
                  </div>
                ) : (
                  <div className="text-xs text-slate-500">拖拽文件或点击上传补充材料（可选）</div>
                )}
              </div>
            </div>

            {error && (
              <div className="mb-3 flex items-center gap-2 text-red-400 text-sm p-3 rounded-lg" style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}>
                <AlertCircle size={14} /> {error}
              </div>
            )}

            <button
              onClick={handleSubmit}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-semibold text-sm transition-all"
              style={{
                background: loading ? 'rgba(245,158,11,0.3)' : 'linear-gradient(135deg, #f59e0b, #d97706)',
                color: loading ? 'rgba(255,255,255,0.5)' : '#000',
                cursor: loading ? 'not-allowed' : 'pointer',
              }}
            >
              {loading ? (
                <><div className="spinner w-4 h-4" /> 正在初始化分析...</>
              ) : (
                <><Zap size={14} /> 启动 CrewAI 情报分析 <ArrowRight size={14} /></>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ─── Sub-components ─── */

function KpiCard({ icon: Icon, label, value, suffix, color, loading }) {
  const colorMap = {
    amber: 'from-amber-500/10 to-amber-500/5 border-amber-500/15 text-amber-400',
    blue: 'from-blue-500/10 to-blue-500/5 border-blue-500/15 text-blue-400',
    emerald: 'from-emerald-500/10 to-emerald-500/5 border-emerald-500/15 text-emerald-400',
    purple: 'from-purple-500/10 to-purple-500/5 border-purple-500/15 text-purple-400',
  }
  const cls = colorMap[color] || colorMap.amber
  return (
    <div className={`p-4 rounded-2xl border bg-gradient-to-br ${cls}`}>
      <div className="flex items-center gap-2 mb-2">
        <Icon size={13} />
        <span className="text-xs font-medium text-slate-400">{label}</span>
      </div>
      {loading ? (
        <div className="h-7 w-16 rounded bg-white/5 animate-pulse" />
      ) : (
        <div className="text-2xl font-bold text-white tracking-tight">
          {typeof value === 'number' ? value.toLocaleString() : value}
          <span className="text-sm text-slate-500 ml-1">{suffix}</span>
        </div>
      )}
    </div>
  )
}

function NavCard({ icon: Icon, title, desc, color, onClick, badge }) {
  const colorMap = {
    blue: 'hover:border-blue-500/30 hover:bg-blue-500/5',
    amber: 'hover:border-amber-500/30 hover:bg-amber-500/5',
    red: 'hover:border-red-500/30 hover:bg-red-500/5',
    slate: 'hover:border-slate-500/30 hover:bg-slate-500/5',
  }
  return (
    <button
      onClick={onClick}
      className={`p-4 rounded-2xl text-left transition-all border border-white/5 bg-white/[0.02] ${colorMap[color]}`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="p-2 rounded-xl bg-white/[0.03] border border-white/5">
          <Icon size={16} className="text-slate-300" />
        </div>
        <ChevronRight size={14} className="text-slate-600" />
      </div>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-sm font-semibold text-white">{title}</span>
        {badge !== null && (
          <span className="w-4 h-4 rounded-full bg-red-500 text-[9px] text-white font-bold flex items-center justify-center">
            {badge}
          </span>
        )}
      </div>
      <p className="text-[11px] text-slate-500">{desc}</p>
    </button>
  )
}

function SkeletonBlock() {
  return (
    <div className="space-y-3 py-2">
      <div className="h-4 w-3/4 rounded bg-white/5 animate-pulse" />
      <div className="h-3 w-1/2 rounded bg-white/5 animate-pulse" />
      <div className="h-3 w-2/3 rounded bg-white/5 animate-pulse" />
    </div>
  )
}
