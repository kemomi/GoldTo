import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Bell, AlertTriangle, CheckCircle, XCircle, Clock,
  ExternalLink, Filter, RotateCcw, Zap, Target, TrendingUp,
} from 'lucide-react'
import { listAlerts, getAlertStats } from '../api/alert'

const CATEGORY_NAMES = {
  geopolitics: '地缘政治', market: '市场动态', policy: '政策监管',
  competitor: '竞争对手', social: '社交媒体', product: '产品趋势',
  legal: '法律合规', tech: '科技创新', energy: '能源',
}

const CATEGORY_COLORS = {
  geopolitics: 'text-red-400 bg-red-500/10 border-red-500/20',
  market: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  policy: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  competitor: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
  social: 'text-pink-400 bg-pink-500/10 border-pink-500/20',
  product: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
  legal: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
  tech: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  energy: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
}

export default function AlertHistoryPage() {
  const navigate = useNavigate()
  const [alerts, setAlerts] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState(null)
  const [statusFilter, setStatusFilter] = useState('all')

  const pageSize = 20

  const fetchData = async (p = page) => {
    setLoading(true)
    try {
      const [alertsRes, statsRes] = await Promise.all([
        listAlerts({ page: p, page_size: pageSize, status: statusFilter }),
        getAlertStats(),
      ])
      if (alertsRes.success) {
        setAlerts(alertsRes.alerts || [])
        setTotal(alertsRes.total || 0)
      }
      if (statsRes.success) setStats(statsRes.data)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchData(1)
  }, [statusFilter])

  const totalPages = Math.ceil(total / pageSize)

  const getPushStatusIcon = (status) => {
    if (!status || Object.keys(status).length === 0) {
      return <Clock size={12} className="text-slate-500" />
    }
    const values = Object.values(status)
    if (values.some(v => v === 'sent')) {
      return <CheckCircle size={12} className="text-green-400" />
    }
    return <XCircle size={12} className="text-red-400" />
  }

  const getPushStatusText = (status) => {
    if (!status || Object.keys(status).length === 0) return '待推送'
    const entries = Object.entries(status)
    const sent = entries.filter(([, v]) => v === 'sent').length
    const total = entries.length
    return sent === total ? '推送成功' : `${sent}/${total} 成功`
  }

  return (
    <div className="min-h-full p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Bell size={24} className="text-amber-400" />
          <div>
            <h1 className="text-2xl font-bold text-white">情报预警历史</h1>
            <p className="text-slate-500 text-sm">实时告警触发记录与推送状态</p>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <StatCard icon={Zap} label="今日告警" value={stats.today_total} color="amber" />
          <StatCard icon={CheckCircle} label="今日已推送" value={stats.today_sent} color="green" />
          <StatCard icon={TrendingUp} label="累计告警" value={stats.total_all} color="blue" />
        </div>
      )}

      {/* Filter Bar */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <Filter size={12} />
          状态筛选
        </div>
        <div className="flex items-center gap-2">
          {[
            { value: 'all', label: '全部' },
            { value: 'sent', label: '已推送' },
            { value: 'failed', label: '失败' },
            { value: 'pending', label: '待推送' },
          ].map(opt => (
            <button
              key={opt.value}
              onClick={() => setStatusFilter(opt.value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                statusFilter === opt.value
                  ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                  : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <button
          onClick={() => { setStatusFilter('all'); fetchData(1); }}
          className="ml-auto flex items-center gap-1 text-xs text-slate-500 hover:text-slate-300 transition-colors"
        >
          <RotateCcw size={12} />
          刷新
        </button>
      </div>

      {/* Alert List */}
      <div className="rounded-xl overflow-hidden" style={{ background: 'var(--dark-800)', border: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="grid grid-cols-12 gap-4 px-6 py-3 text-xs text-slate-500 font-medium border-b border-white/5">
          <div className="col-span-2">触发时间</div>
          <div className="col-span-5">事件</div>
          <div className="col-span-2">触发原因</div>
          <div className="col-span-2">推送状态</div>
          <div className="col-span-1"></div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="spinner w-5 h-5" />
          </div>
        ) : alerts.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-12 h-12 rounded-xl bg-amber-500/5 flex items-center justify-center mx-auto mb-3 border border-amber-500/10">
              <Bell size={20} className="text-amber-400/40" />
            </div>
            <div className="text-slate-500 text-sm">暂无告警记录</div>
            <div className="text-slate-600 text-xs mt-1">当事件满足预警规则时，会在此显示</div>
          </div>
        ) : (
          alerts.map(alert => (
            <div
              key={alert.id}
              className="grid grid-cols-12 gap-4 px-6 py-4 text-sm border-b border-white/5 hover:bg-white/[0.02] transition-colors"
            >
              <div className="col-span-2">
                <div className="text-xs text-slate-300">
                  {alert.triggered_at ? new Date(alert.triggered_at).toLocaleString('zh-CN', {
                    month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit'
                  }) : '--'}
                </div>
                <div className="text-[10px] text-slate-600 mt-0.5">
                  {alert.triggered_at ? new Date(alert.triggered_at).toLocaleDateString('zh-CN', { weekday: 'short' }) : ''}
                </div>
              </div>

              <div className="col-span-5 min-w-0">
                <div className="flex items-start gap-2 mb-1.5">
                  <span className={`shrink-0 text-[10px] px-1.5 py-0.5 rounded-full border ${
                    CATEGORY_COLORS[alert.event_category] || 'bg-slate-500/10 text-slate-400 border-slate-500/20'
                  }`}>
                    {CATEGORY_NAMES[alert.event_category] || alert.event_category}
                  </span>
                  {alert.event_url ? (
                    <a href={alert.event_url} target="_blank" rel="noopener noreferrer"
                      className="text-sm font-medium text-white leading-snug truncate hover:text-amber-400 transition-colors group/link">
                      {alert.event_title}
                      <ExternalLink size={11} className="inline-block ml-1 text-slate-500 group-hover/link:text-amber-400 transition-colors" />
                    </a>
                  ) : (
                    <h4 className="text-sm font-medium text-white leading-snug truncate">
                      {alert.event_title}
                    </h4>
                  )}
                </div>
                <div className="flex items-center gap-2 text-[11px] text-slate-500">
                  <span>{alert.event_source}</span>
                  <span>·</span>
                  <span className="text-slate-400">相关度 {(alert.event_relevance * 100).toFixed(0)}%</span>
                </div>
              </div>

              <div className="col-span-2">
                <div className="flex items-center gap-1.5">
                  {alert.matched_reason === 'relevance' ? (
                    <Target size={12} className="text-amber-400" />
                  ) : (
                    <Zap size={12} className="text-blue-400" />
                  )}
                  <span className="text-xs text-slate-300">
                    {alert.matched_reason === 'relevance'
                      ? `相关度 ≥ 阈值`
                      : '命中关键词'}
                  </span>
                </div>
              </div>

              <div className="col-span-2">
                <div className="flex items-center gap-1.5">
                  {getPushStatusIcon(alert.push_status)}
                  <span className="text-xs text-slate-400">{getPushStatusText(alert.push_status)}</span>
                </div>
                {alert.push_status && Object.keys(alert.push_status).length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {Object.entries(alert.push_status).map(([ch, st]) => (
                      <span key={ch} className={`text-[9px] px-1 py-0.5 rounded ${
                        st === 'sent' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
                      }`}>
                        {ch}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="col-span-1 flex items-center justify-end">
                {alert.event_url && (
                  <a
                    href={alert.event_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={e => e.stopPropagation()}
                    className="p-1.5 rounded-lg text-slate-500 hover:text-amber-400 hover:bg-amber-500/10 transition-all"
                  >
                    <ExternalLink size={14} />
                  </a>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2 mt-6">
          <button
            onClick={() => fetchData(Math.max(1, page - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            上一页
          </button>
          {Array.from({ length: totalPages }, (_, i) => (
            <button
              key={i}
              onClick={() => fetchData(i + 1)}
              className={`w-8 h-8 rounded-lg text-xs font-medium transition-all ${
                page === i + 1
                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                  : 'text-slate-500 hover:bg-white/5'
              }`}
            >
              {i + 1}
            </button>
          ))}
          <button
            onClick={() => fetchData(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            className="px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            下一页
          </button>
        </div>
      )}
    </div>
  )
}

function StatCard({ icon: Icon, label, value, color }) {
  const colorMap = {
    amber: 'from-amber-500/10 to-amber-500/5 border-amber-500/15 text-amber-400',
    green: 'from-emerald-500/10 to-emerald-500/5 border-emerald-500/15 text-emerald-400',
    blue: 'from-blue-500/10 to-blue-500/5 border-blue-500/15 text-blue-400',
  }
  const cls = colorMap[color] || colorMap.amber
  return (
    <div className={`p-4 rounded-2xl border bg-gradient-to-br ${cls}`}>
      <div className="flex items-center gap-2 mb-2">
        <Icon size={14} />
        <span className="text-xs font-medium text-slate-400">{label}</span>
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
    </div>
  )
}
