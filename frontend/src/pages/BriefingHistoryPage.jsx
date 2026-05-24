import React, { useState, useEffect, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  Newspaper, Calendar, ChevronRight, Filter, RefreshCw,
  Clock, CheckCircle, AlertCircle, XCircle, Send, Eye,
  Search, X, SlidersHorizontal, RotateCcw,
} from 'lucide-react'
import { listBriefings, generateBriefingNow, getTodayBriefingStatus } from '../api/briefing'

/* ─── Constants ─── */

const CATEGORY_OPTIONS = [
  { value: 'geopolitics', label: '地缘政治' },
  { value: 'market', label: '市场动态' },
  { value: 'policy', label: '政策监管' },
  { value: 'competitor', label: '竞争对手' },
  { value: 'social', label: '社交媒体' },
  { value: 'product', label: '产品趋势' },
  { value: 'legal', label: '法律合规' },
  { value: 'tech', label: '科技创新' },
  { value: 'energy', label: '能源' },
]

/* ─── Helpers ─── */

function highlightText(text, keyword) {
  if (!keyword || !text) return text
  try {
    const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const parts = text.split(new RegExp(`(${escaped})`, 'gi'))
    return parts.map((part, i) =>
      part.toLowerCase() === keyword.toLowerCase()
        ? <mark key={i} className="bg-amber-500/20 text-amber-400 rounded px-0.5">{part}</mark>
        : part
    )
  } catch {
    return text
  }
}

function buildFilterLabel(params) {
  const parts = []
  if (params.q) parts.push(`关键词: "${params.q}"`)
  if (params.date_from || params.date_to) {
    parts.push(`日期: ${params.date_from || '...'} ~ ${params.date_to || '...'}`)
  }
  if (params.category) parts.push(`类别: ${CATEGORY_OPTIONS.find(c => c.value === params.category)?.label || params.category}`)
  if (params.source) parts.push(`来源: ${params.source}`)
  if (params.min_relevance) parts.push(`相关度 ≥ ${(params.min_relevance * 100).toFixed(0)}%`)
  return parts.length > 0 ? parts.join(' · ') : null
}

/* ─── Component ─── */

export default function BriefingHistoryPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  // Read initial filters from URL
  const getInitialFilters = useCallback(() => ({
    q: searchParams.get('q') || '',
    date_from: searchParams.get('date_from') || '',
    date_to: searchParams.get('date_to') || '',
    category: searchParams.get('category') || '',
    source: searchParams.get('source') || '',
    min_relevance: searchParams.get('min_relevance') ? parseFloat(searchParams.get('min_relevance')) : '',
  }), [searchParams])

  const [filters, setFilters] = useState(getInitialFilters)
  const [showFilters, setShowFilters] = useState(false)
  const [briefings, setBriefings] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(parseInt(searchParams.get('page') || '1', 10))
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [todayStatus, setTodayStatus] = useState(null)
  const [pollTimer, setPollTimer] = useState(null)

  const pageSize = 10
  const hasActiveFilters = Object.values(filters).some(v => v !== '' && v !== null && v !== undefined)

  const fetchData = useCallback(async (p = page, currentFilters = filters) => {
    setLoading(true)
    try {
      const apiParams = { page: p, page_size: pageSize }
      if (currentFilters.q) apiParams.q = currentFilters.q
      if (currentFilters.date_from) apiParams.date_from = currentFilters.date_from
      if (currentFilters.date_to) apiParams.date_to = currentFilters.date_to
      if (currentFilters.category) apiParams.category = currentFilters.category
      if (currentFilters.source) apiParams.source = currentFilters.source
      if (currentFilters.min_relevance !== '' && currentFilters.min_relevance !== null) {
        apiParams.min_relevance = currentFilters.min_relevance
      }

      const [listRes, todayRes] = await Promise.all([
        listBriefings(apiParams),
        getTodayBriefingStatus(),
      ])
      setBriefings(listRes.briefings || [])
      setTotal(listRes.total || 0)
      setTodayStatus(todayRes)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }, [page, filters])

  useEffect(() => {
    fetchData(page, filters)
    return () => {
      if (pollTimer) clearInterval(pollTimer)
    }
  }, [])

  // Sync URL when filters/page change
  const applyFilters = useCallback((newFilters, newPage = 1) => {
    setFilters(newFilters)
    setPage(newPage)

    const sp = new URLSearchParams()
    if (newFilters.q) sp.set('q', newFilters.q)
    if (newFilters.date_from) sp.set('date_from', newFilters.date_from)
    if (newFilters.date_to) sp.set('date_to', newFilters.date_to)
    if (newFilters.category) sp.set('category', newFilters.category)
    if (newFilters.source) sp.set('source', newFilters.source)
    if (newFilters.min_relevance !== '' && newFilters.min_relevance !== null) {
      sp.set('min_relevance', String(newFilters.min_relevance))
    }
    if (newPage > 1) sp.set('page', String(newPage))
    setSearchParams(sp)

    fetchData(newPage, newFilters)
  }, [fetchData, setSearchParams])

  const handleSearch = () => applyFilters({ ...filters })

  const handleReset = () => {
    const empty = { q: '', date_from: '', date_to: '', category: '', source: '', min_relevance: '' }
    setShowFilters(false)
    applyFilters(empty, 1)
  }

  const handlePageChange = (newPage) => {
    setPage(newPage)
    applyFilters(filters, newPage)
  }

  const startPolling = () => {
    if (pollTimer) clearInterval(pollTimer)
    const timer = setInterval(async () => {
      try {
        const res = await getTodayBriefingStatus()
        setTodayStatus(res)
        if (res.status === 'completed' || res.status === 'failed' || res.status === 'not_started') {
          clearInterval(timer)
          setPollTimer(null)
          setGenerating(false)
          fetchData(page, filters)
        }
      } catch (e) {
        console.error(e)
      }
    }, 3000)
    setPollTimer(timer)
  }

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      await generateBriefingNow()
      setTodayStatus(prev => prev ? { ...prev, status: 'generating' } : { date: '', status: 'generating' })
      startPolling()
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
    const map = { completed: '已完成', generating: '生成中', draft: '草稿', failed: '失败', sent: '已推送' }
    return map[status] || status
  }

  const filterLabel = buildFilterLabel(filters)
  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="min-h-full p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Newspaper size={24} className="text-amber-400" />
          <div>
            <h1 className="text-2xl font-bold text-white">每日战略简报</h1>
            <p className="text-slate-500 text-sm">查看历史简报和生成状态</p>
          </div>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all"
          style={{
            background: generating ? 'rgba(245,158,11,0.3)' : 'linear-gradient(135deg, #f59e0b, #d97706)',
            color: '#000',
            cursor: generating ? 'not-allowed' : 'pointer',
          }}
        >
          <RefreshCw size={14} className={generating ? 'animate-spin' : ''} />
          {generating ? '生成中...' : '立即生成今日简报'}
        </button>
      </div>

      {/* Search Bar */}
      <div className="mb-4">
        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={filters.q}
              onChange={e => setFilters(f => ({ ...f, q: e.target.value }))}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder="搜索简报标题、摘要、内容关键词..."
              className="w-full pl-10 pr-10 py-2.5 rounded-xl text-sm text-white placeholder-slate-500 border border-white/10 focus:border-amber-500/30 focus:outline-none transition-colors"
              style={{ background: 'var(--dark-800)' }}
            />
            {filters.q && (
              <button
                onClick={() => { setFilters(f => ({ ...f, q: '' })); if (filters.q) handleSearch() }}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white"
              >
                <X size={14} />
              </button>
            )}
          </div>
          <button
            onClick={() => setShowFilters(s => !s)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium border transition-all ${
              showFilters || hasActiveFilters
                ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                : 'text-slate-400 border-white/10 hover:border-white/20 hover:text-slate-200'
            }`}
            style={{ background: 'var(--dark-800)' }}
          >
            <SlidersHorizontal size={14} />
            筛选
            {hasActiveFilters && (
              <span className="w-4 h-4 rounded-full bg-amber-500 text-[10px] text-black font-bold flex items-center justify-center">
                {Object.values(filters).filter(v => v !== '' && v !== null && v !== undefined).length}
              </span>
            )}
          </button>
          <button
            onClick={handleSearch}
            className="px-5 py-2.5 rounded-xl text-sm font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 hover:bg-amber-500/20 transition-all"
          >
            搜索
          </button>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div className="mt-3 p-4 rounded-xl border border-white/10" style={{ background: 'var(--dark-800)' }}>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Date Range */}
              <div>
                <label className="block text-xs text-slate-500 mb-1.5">日期范围</label>
                <div className="flex items-center gap-2">
                  <input
                    type="date"
                    value={filters.date_from}
                    onChange={e => setFilters(f => ({ ...f, date_from: e.target.value }))}
                    className="flex-1 px-2.5 py-1.5 rounded-lg text-xs text-white border border-white/10 bg-black/20 focus:border-amber-500/30 focus:outline-none"
                  />
                  <span className="text-slate-500 text-xs">~</span>
                  <input
                    type="date"
                    value={filters.date_to}
                    onChange={e => setFilters(f => ({ ...f, date_to: e.target.value }))}
                    className="flex-1 px-2.5 py-1.5 rounded-lg text-xs text-white border border-white/10 bg-black/20 focus:border-amber-500/30 focus:outline-none"
                  />
                </div>
              </div>

              {/* Category */}
              <div>
                <label className="block text-xs text-slate-500 mb-1.5">事件类别</label>
                <select
                  value={filters.category}
                  onChange={e => setFilters(f => ({ ...f, category: e.target.value }))}
                  className="w-full px-2.5 py-1.5 rounded-lg text-xs text-white border border-white/10 bg-black/20 focus:border-amber-500/30 focus:outline-none appearance-none"
                >
                  <option value="">全部类别</option>
                  {CATEGORY_OPTIONS.map(c => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </select>
              </div>

              {/* Source */}
              <div>
                <label className="block text-xs text-slate-500 mb-1.5">信息来源</label>
                <input
                  type="text"
                  value={filters.source}
                  onChange={e => setFilters(f => ({ ...f, source: e.target.value }))}
                  placeholder="如: 36氪, BBC"
                  className="w-full px-2.5 py-1.5 rounded-lg text-xs text-white placeholder-slate-600 border border-white/10 bg-black/20 focus:border-amber-500/30 focus:outline-none"
                />
              </div>

              {/* Min Relevance */}
              <div>
                <label className="block text-xs text-slate-500 mb-1.5">
                  最小相关度: {filters.min_relevance !== '' ? `${(filters.min_relevance * 100).toFixed(0)}%` : '不限'}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={filters.min_relevance !== '' ? filters.min_relevance : 0}
                  onChange={e => setFilters(f => ({ ...f, min_relevance: parseFloat(e.target.value) }))}
                  className="w-full accent-amber-500"
                />
                <div className="flex justify-between text-[10px] text-slate-600 mt-0.5">
                  <span>0%</span>
                  <span>50%</span>
                  <span>100%</span>
                </div>
              </div>
            </div>

            <div className="flex justify-end mt-4">
              <button
                onClick={handleReset}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-white hover:bg-white/5 transition-all"
              >
                <RotateCcw size={12} />
                重置筛选
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Results Info */}
      {filterLabel && (
        <div className="mb-3 flex items-center gap-2 text-xs text-slate-400">
          <Filter size={12} className="text-amber-400/60" />
          <span>筛选条件: {filterLabel}</span>
          <span className="text-slate-600">·</span>
          <span>共 {total} 条结果</span>
        </div>
      )}

      {/* 今日状态卡片 */}
      {todayStatus && (
        <div className="mb-6 p-4 rounded-xl flex items-center justify-between"
          style={{ background: 'var(--dark-800)', border: '1px solid rgba(255,255,255,0.06)' }}>
          <div className="flex items-center gap-3">
            <Calendar size={18} className="text-amber-400" />
            <div>
              <div className="text-sm font-medium text-white">{todayStatus.date} 简报</div>
              <div className="text-xs text-slate-500">
                {todayStatus.status === 'not_started'
                  ? '尚未生成 — 点击右上角按钮开始'
                  : todayStatus.status === 'generating'
                  ? '正在生成中，请稍候...'
                  : `状态: ${statusText(todayStatus.status)} · 事件数: ${todayStatus.events_count || 0}`}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {todayStatus.status === 'completed' && todayStatus.briefing_id && (
              <button
                onClick={() => navigate(`/briefing/${todayStatus.briefing_id}`)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-amber-500/30 text-amber-400 hover:bg-amber-500/10 transition-all"
              >
                <Eye size={12} /> 查看简报
              </button>
            )}
            <div className="flex items-center gap-2">
              {statusIcon(todayStatus.status)}
              <span className="text-xs text-slate-400">{statusText(todayStatus.status)}</span>
            </div>
          </div>
        </div>
      )}

      {/* 简报列表 */}
      <div className="rounded-xl overflow-hidden" style={{ background: 'var(--dark-800)', border: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="grid grid-cols-12 gap-4 px-6 py-3 text-xs text-slate-500 font-medium border-b border-white/5">
          <div className="col-span-2">日期</div>
          <div className="col-span-4">标题</div>
          <div className="col-span-2">事件/来源</div>
          <div className="col-span-2">状态</div>
          <div className="col-span-2">推送</div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="spinner w-5 h-5" />
          </div>
        ) : briefings.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-slate-500 text-sm mb-2">
              {hasActiveFilters ? '未找到匹配的简报' : '暂无简报记录'}
            </div>
            {hasActiveFilters && (
              <button
                onClick={handleReset}
                className="text-xs text-amber-400 hover:text-amber-300 underline underline-offset-2"
              >
                清除筛选条件
              </button>
            )}
          </div>
        ) : (
          briefings.map(b => (
            <div
              key={b.briefing_id}
              onClick={() => navigate(`/briefing/${b.briefing_id}`)}
              className="grid grid-cols-12 gap-4 px-6 py-4 text-sm border-b border-white/5 hover:bg-white/[0.02] cursor-pointer transition-colors"
            >
              <div className="col-span-2 text-slate-400">{b.date}</div>
              <div className="col-span-4 text-white font-medium truncate">
                {highlightText(b.title || '每日战略简报', filters.q)}
              </div>
              <div className="col-span-2 text-slate-500">
                {b.events_count} / {b.sources_count}
              </div>
              <div className="col-span-2 flex items-center gap-1.5">
                {statusIcon(b.status)}
                <span className="text-slate-400">{statusText(b.status)}</span>
              </div>
              <div className="col-span-2 flex items-center gap-1.5">
                {Object.entries(b.push_status || {}).map(([ch, st]) => (
                  <span key={ch} className={`text-[10px] px-1.5 py-0.5 rounded ${
                    st === 'sent' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
                  }`}>
                    {ch}
                  </span>
                ))}
                {!b.push_status || Object.keys(b.push_status).length === 0 ? (
                  <span className="text-slate-600 text-xs">未推送</span>
                ) : null}
              </div>
            </div>
          ))
        )}
      </div>

      {/* 分页 */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2 mt-6">
          <button
            onClick={() => handlePageChange(Math.max(1, page - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            上一页
          </button>
          {Array.from({ length: totalPages }, (_, i) => (
            <button
              key={i}
              onClick={() => handlePageChange(i + 1)}
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
            onClick={() => handlePageChange(Math.min(totalPages, page + 1))}
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
