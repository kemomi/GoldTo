import React, { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, Zap, ArrowRight, FileText, Target, Settings2, AlertCircle, Filter, History } from 'lucide-react'
import { createSession, uploadSeed, startSimulation, getLastSessionId, saveLastSessionId } from '../api/client'

const EXAMPLES = [
  { icon: '🌏', label: '每日简报', goal: '生成周大福今日海外市场战略简报，覆盖东南亚、日韩、北美、中东与澳洲。' },
  { icon: '🏬', label: '新市场进入', goal: '评估周大福进入迪拜、多哈和澳大利亚市场的机会、风险与优先级。' },
  { icon: '💍', label: '产品组合', goal: '分析高金价环境下周大福海外市场应如何调整黄金、婚嫁、钻石和定制产品组合。' },
  { icon: '⚖️', label: '合规预警', goal: '识别周大福海外门店、电商和营销活动需要关注的贵金属认证、AML和数据隐私风险。' },
]

export default function HomePage() {
  const navigate = useNavigate()
  const fileRef = useRef()

  const [file, setFile] = useState(null)
  const [goal, setGoal] = useState('')
  const [rounds, setRounds] = useState(20)
  const [agents, setAgents] = useState(10)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)

  const handleDrop = e => {
    e.preventDefault()
    const f = e.dataTransfer.files[0]
    if (f) setFile(f)
  }

  const handleSubmit = async () => {
    if (!file) return setError('请上传种子文档')
    if (!goal.trim()) return setError('请输入情报任务')
    setError('')
    setLoading(true)

    try {
      const { session_id } = await createSession()

      const fd = new FormData()
      fd.append('file', file)
      fd.append('prediction_goal', goal)
      fd.append('rounds', rounds)
      fd.append('agents_count', agents)
      await uploadSeed(session_id, fd)

      await startSimulation(session_id)
      saveLastSessionId(session_id)
      navigate(`/simulate/${session_id}`)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
      setLoading(false)
    }
  }

  return (
    <div className="min-h-full flex flex-col items-center justify-center p-8">
      {/* Hero */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-amber-500/30 bg-amber-500/5 text-amber-400 text-xs font-medium mb-6">
          <Zap size={12} /> 周大福海外市场 · 战略情报雷达
        </div>
        <h1 className="text-5xl font-bold mb-3 gold-text-glow" style={{ color: 'var(--gold-bright)' }}>
          CTF Strategy Radar
        </h1>
        <p className="text-slate-400 text-lg max-w-xl mx-auto">
          上传企业调研或公开资料，让多位企业专家 Agent 会商海外市场变化、风险预警和部门行动建议
        </p>
      </div>

      {/* Form card */}
      <div className="w-full max-w-2xl gradient-border p-[1px]">
        <div className="rounded-xl p-8" style={{ background: 'var(--dark-800)' }}>

          {/* Step 1: Upload */}
          <div className="mb-6">
            <label className="flex items-center gap-2 text-sm font-semibold text-slate-300 mb-3">
              <FileText size={15} className="text-amber-400" />
              Step 1 · 上传企业调研 / 公开资料
            </label>
            <div
              className="border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all"
              style={{ borderColor: file ? 'rgba(245,158,11,0.5)' : 'rgba(255,255,255,0.1)', background: file ? 'rgba(245,158,11,0.03)' : 'transparent' }}
              onDrop={handleDrop}
              onDragOver={e => e.preventDefault()}
              onClick={() => fileRef.current?.click()}
            >
              <input
                ref={fileRef}
                type="file"
                accept=".txt,.pdf,.md"
                className="hidden"
                onChange={e => setFile(e.target.files[0])}
              />
              {file ? (
                <div className="flex items-center justify-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
                    <FileText size={20} className="text-amber-400" />
                  </div>
                  <div className="text-left">
                    <div className="text-white font-medium text-sm">{file.name}</div>
                    <div className="text-slate-500 text-xs">{(file.size / 1024).toFixed(1)} KB</div>
                  </div>
                </div>
              ) : (
                <>
                  <Upload size={28} className="mx-auto mb-3 text-slate-600" />
                  <div className="text-slate-400 text-sm">拖拽文件或点击上传</div>
                  <div className="text-slate-600 text-xs mt-1">支持 .txt · .pdf · .md</div>
                </>
              )}
            </div>
          </div>

          {/* Step 2: Goal */}
          <div className="mb-6">
            <label className="flex items-center gap-2 text-sm font-semibold text-slate-300 mb-3">
              <Target size={15} className="text-amber-400" />
              Step 2 · 描述情报任务
            </label>
            <textarea
              className="w-full rounded-xl px-4 py-3 text-sm resize-none outline-none transition-all"
              style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                color: 'var(--text-primary)',
                minHeight: 80,
              }}
              placeholder="例如：生成周大福今日海外市场战略简报，覆盖机会、风险、竞品、产品、渠道、合规和行动清单。"
              value={goal}
              onChange={e => setGoal(e.target.value)}
              onFocus={e => e.target.style.borderColor = 'rgba(245,158,11,0.4)'}
              onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.08)'}
            />
            {/* Quick examples */}
            <div className="flex flex-wrap gap-2 mt-2">
              {EXAMPLES.map(ex => (
                <button
                  key={ex.label}
                  onClick={() => setGoal(ex.goal)}
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

          {/* Advanced settings */}
          <div className="mb-6">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-2 text-xs text-slate-500 hover:text-slate-300 transition-colors"
            >
              <Settings2 size={13} />
              高级设置 {showAdvanced ? '▲' : '▼'}
            </button>
            {showAdvanced && (
              <div className="mt-3 grid grid-cols-2 gap-4 p-4 rounded-xl" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                <div>
                  <label className="text-xs text-slate-400 mb-1 block">会商轮次 ({rounds})</label>
                  <input type="range" min={5} max={100} value={rounds} onChange={e => setRounds(+e.target.value)} className="w-full accent-amber-500" />
                </div>
                <div>
                  <label className="text-xs text-slate-400 mb-1 block">智能体数量 ({agents})</label>
                  <input type="range" min={4} max={30} value={agents} onChange={e => setAgents(+e.target.value)} className="w-full accent-amber-500" />
                </div>
              </div>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="mb-4 flex items-center gap-2 text-red-400 text-sm p-3 rounded-lg" style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}>
              <AlertCircle size={15} /> {error}
            </div>
          )}

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full flex items-center justify-center gap-3 py-3.5 rounded-xl font-semibold text-sm transition-all"
            style={{
              background: loading ? 'rgba(245,158,11,0.3)' : 'linear-gradient(135deg, #f59e0b, #d97706)',
              color: loading ? 'rgba(255,255,255,0.5)' : '#000',
              cursor: loading ? 'not-allowed' : 'pointer',
              boxShadow: loading ? 'none' : '0 4px 20px rgba(245,158,11,0.3)',
            }}
          >
            {loading ? (
              <>
                <div className="spinner w-4 h-4" />
                正在初始化情报会商...
              </>
            ) : (
              <>
                <Zap size={16} />
                启动战略情报会商
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </div>
      </div>

      <button
        onClick={() => navigate('/worldmonitor')}
        className="mt-4 flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-sm transition-all"
        style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#cbd5e1' }}
      >
        <Filter size={15} className="text-amber-400" />
        从 WorldMonitor 导入并人工审核情报
      </button>

      <div className="mt-3 flex flex-wrap justify-center gap-3">
        {getLastSessionId() && (
          <button
            onClick={() => navigate(`/report/${getLastSessionId()}`)}
            className="flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-sm transition-all"
            style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.18)', color: '#fbbf24' }}
          >
            <FileText size={15} />
            继续查看最近简报
          </button>
        )}
        <button
          onClick={() => navigate('/history')}
          className="flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-sm transition-all"
          style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#cbd5e1' }}
        >
          <History size={15} className="text-amber-400" />
          查看历史会话
        </button>
      </div>

      {/* Workflow steps */}
      <div className="mt-10 grid grid-cols-5 gap-3 max-w-2xl w-full">
        {[
          { step: '01', label: '图谱构建', desc: 'GraphRAG' },
          { step: '02', label: '专家生成', desc: '企业职能' },
          { step: '03', label: '情报会商', desc: '机会风险' },
          { step: '04', label: '简报生成', desc: '行动清单' },
          { step: '05', label: '追问验证', desc: '证据链' },
        ].map((s, i) => (
          <div key={i} className="text-center">
            <div className="text-xs font-mono text-amber-500/40 mb-1">{s.step}</div>
            <div className="text-xs font-semibold text-slate-300">{s.label}</div>
            <div className="text-xs text-slate-600">{s.desc}</div>
            {i < 4 && <div className="text-amber-500/20 text-xs mt-1">↓</div>}
          </div>
        ))}
      </div>
    </div>
  )
}
