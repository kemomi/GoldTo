import React, { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, Zap, ArrowRight, FileText, Target, Settings2, AlertCircle } from 'lucide-react'
import { createSession, uploadSeed, startSimulation } from '../api/client'

const EXAMPLES = [
  { icon: '🥇', label: '黄金价格', goal: '未来3个月国际黄金价格走势将如何变化？' },
  { icon: '🛢️', label: '原油市场', goal: '未来6个月WTI原油价格将如何演变？' },
  { icon: '💹', label: 'A股行情', goal: '未来一季度A股市场整体走势如何？' },
  { icon: '🌏', label: '地缘政治', goal: '该地区紧张局势将如何影响全球金融市场？' },
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
    if (!goal.trim()) return setError('请输入预测目标')
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
      navigate(`/simulate/${session_id}`)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
      setLoading(false)
    }
  }

  return (
    <div className="min-h-full flex flex-col items-center justify-center p-8">
      {/* Hero */}
      <div className="text-center mb-10 animate-float">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-amber-500/30 bg-amber-500/5 text-amber-400 text-xs font-medium mb-6">
          <Zap size={12} /> 群体智能预测引擎 · Swarm Intelligence
        </div>
        <h1 className="text-5xl font-bold mb-3 gold-text-glow" style={{ color: 'var(--gold-bright)' }}>
          GoldTo
        </h1>
        <p className="text-slate-400 text-lg max-w-xl mx-auto">
          上传种子材料，描述预测需求，让成千上万个 AI 智能体在数字沙盘中预演未来
        </p>
      </div>

      {/* Form card */}
      <div className="w-full max-w-2xl gradient-border p-[1px]">
        <div className="rounded-xl p-8" style={{ background: 'var(--dark-800)' }}>

          {/* Step 1: Upload */}
          <div className="mb-6">
            <label className="flex items-center gap-2 text-sm font-semibold text-slate-300 mb-3">
              <FileText size={15} className="text-amber-400" />
              Step 1 · 上传种子材料
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
              Step 2 · 描述预测目标
            </label>
            <textarea
              className="w-full rounded-xl px-4 py-3 text-sm resize-none outline-none transition-all"
              style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                color: 'var(--text-primary)',
                minHeight: 80,
              }}
              placeholder="例如：未来3个月国际黄金价格走势将如何变化？"
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
                  <label className="text-xs text-slate-400 mb-1 block">仿真轮次 ({rounds})</label>
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
                正在初始化仿真...
              </>
            ) : (
              <>
                <Zap size={16} />
                启动群体智能仿真
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </div>
      </div>

      {/* Workflow steps */}
      <div className="mt-10 grid grid-cols-5 gap-3 max-w-2xl w-full">
        {[
          { step: '01', label: '图谱构建', desc: 'GraphRAG' },
          { step: '02', label: '人设生成', desc: '多元视角' },
          { step: '03', label: '群体仿真', desc: '涌现演化' },
          { step: '04', label: '报告生成', desc: '预测结论' },
          { step: '05', label: '深度互动', desc: '与智能体对话' },
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
