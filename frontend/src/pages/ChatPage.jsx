import React, { useState, useRef, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { MessageCircle, Send, Bot, User, ChevronDown } from 'lucide-react'
import { sendChat, getAgents } from '../api/client'

function ChatBubble({ message }) {
  const isUser = message.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex gap-3 max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold ${
          isUser ? 'bg-amber-500/20 text-amber-400' : 'bg-slate-700 text-slate-300'
        }`}>
          {isUser ? <User size={14} /> : message.agentInitial || <Bot size={14} />}
        </div>
        <div>
          {!isUser && message.agentName && (
            <div className="text-xs text-amber-400/70 mb-1 px-1">{message.agentName}</div>
          )}
          <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser ? 'chat-bubble-user text-amber-100' : 'chat-bubble-ai text-slate-200'
          }`}>
            {message.content}
          </div>
          <div className="text-xs text-slate-600 mt-1 px-1">
            {new Date(message.ts).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
      </div>
    </div>
  )
}

function AgentSelector({ agents, selected, onSelect }) {
  const [open, setOpen] = useState(false)
  const current = selected === 'report'
    ? { name: 'ReportAgent', role: '分析报告智能体' }
    : agents.find(a => a.id === selected)

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm transition-all w-full"
        style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}
      >
        <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
          style={{ background: 'rgba(245,158,11,0.15)', color: '#fbbf24' }}>
          {current?.name?.[0] || 'R'}
        </div>
        <div className="flex-1 text-left">
          <div className="font-medium text-slate-200">{current?.name || '选择对话对象'}</div>
          <div className="text-xs text-slate-500">{current?.role || ''}</div>
        </div>
        <ChevronDown size={14} className="text-slate-500" style={{ transform: open ? 'rotate(180deg)' : '', transition: 'transform 0.2s' }} />
      </button>

      {open && (
        <div className="absolute top-full left-0 right-0 mt-1 rounded-xl overflow-hidden z-10"
          style={{ background: 'var(--dark-700)', border: '1px solid rgba(255,255,255,0.08)', boxShadow: '0 8px 32px rgba(0,0,0,0.5)' }}>
          {/* Report agent option */}
          <button
            onClick={() => { onSelect('report'); setOpen(false) }}
            className="flex items-center gap-3 px-4 py-3 w-full text-sm transition-all hover:bg-white/5"
            style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}
          >
            <div className="w-7 h-7 rounded-full bg-amber-500/20 flex items-center justify-center">
              <Bot size={13} className="text-amber-400" />
            </div>
            <div className="text-left">
              <div className="font-medium text-slate-200">ReportAgent</div>
              <div className="text-xs text-slate-500">分析报告 · 综合视角</div>
            </div>
          </button>
          {/* Individual agents */}
          {agents.map(a => {
            const color = a.current_stance > 0.2 ? '#10b981' : a.current_stance < -0.2 ? '#f87171' : '#94a3b8'
            return (
              <button key={a.id}
                onClick={() => { onSelect(a.id); setOpen(false) }}
                className="flex items-center gap-3 px-4 py-3 w-full text-sm transition-all hover:bg-white/5">
                <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                  style={{ background: 'rgba(255,255,255,0.06)', color: '#e2e8f0' }}>
                  {a.name[0]}
                </div>
                <div className="flex-1 text-left">
                  <div className="font-medium text-slate-200">{a.name}</div>
                  <div className="text-xs text-slate-500">{a.role}</div>
                </div>
                <span className="text-xs font-mono" style={{ color }}>
                  {a.current_stance > 0 ? '+' : ''}{a.current_stance.toFixed(2)}
                </span>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default function ChatPage() {
  const { sessionId } = useParams()
  const [agents, setAgents] = useState([])
  const [selectedAgent, setSelectedAgent] = useState('report')
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '你好！我是 ReportAgent，已完成本次群体智能仿真分析。你可以问我关于预测结论、风险因素、或选择与具体智能体对话。',
      agentName: 'ReportAgent',
      agentInitial: 'R',
      ts: Date.now(),
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef()

  useEffect(() => {
    getAgents(sessionId).then(d => setAgents(d.agents)).catch(console.error)
  }, [sessionId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    const msg = input.trim()
    if (!msg || loading) return
    setInput('')

    const userMsg = { role: 'user', content: msg, ts: Date.now() }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const agentId = selectedAgent === 'report' ? null : selectedAgent
      const { response } = await sendChat(sessionId, msg, agentId)

      const agent = agentId ? agents.find(a => a.id === agentId) : null
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response,
        agentName: agent?.name || 'ReportAgent',
        agentInitial: agent?.name?.[0] || 'R',
        ts: Date.now(),
      }])
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `发生错误：${e.response?.data?.detail || e.message}`,
        agentName: 'System',
        ts: Date.now(),
      }])
    } finally {
      setLoading(false)
    }
  }

  const QUICK_QUESTIONS = [
    '你对这个预测的信心有多高？',
    '最大的下行风险是什么？',
    '有哪些关键信号需要关注？',
    '请给出具体的操作建议',
  ]

  return (
    <div className="p-6 max-w-5xl mx-auto flex flex-col" style={{ height: 'calc(100vh - 0px)' }}>
      <div className="flex items-center gap-3 mb-4">
        <MessageCircle size={24} className="text-amber-400" />
        <h1 className="text-2xl font-bold text-white">深度对话</h1>
      </div>

      <div className="grid grid-cols-4 gap-4 flex-1 min-h-0">
        {/* Sidebar */}
        <div className="col-span-1 flex flex-col gap-4">
          <div>
            <div className="text-xs text-slate-500 mb-2">选择对话对象</div>
            <AgentSelector agents={agents} selected={selectedAgent} onSelect={setSelectedAgent} />
          </div>

          <div>
            <div className="text-xs text-slate-500 mb-2">快捷提问</div>
            <div className="space-y-2">
              {QUICK_QUESTIONS.map((q, i) => (
                <button key={i} onClick={() => setInput(q)}
                  className="w-full text-left text-xs px-3 py-2 rounded-lg transition-all"
                  style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', color: '#94a3b8' }}
                  onMouseEnter={e => e.target.style.borderColor = 'rgba(245,158,11,0.3)'}
                  onMouseLeave={e => e.target.style.borderColor = 'rgba(255,255,255,0.06)'}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Chat area */}
        <div className="col-span-3 flex flex-col glass-card overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-5">
            {messages.map((m, i) => <ChatBubble key={i} message={m} />)}
            {loading && (
              <div className="flex justify-start mb-4">
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
                    <Bot size={14} className="text-slate-300" />
                  </div>
                  <div className="chat-bubble-ai rounded-2xl px-4 py-3 flex items-center gap-2">
                    <div className="flex gap-1">
                      {[0, 1, 2].map(i => (
                        <div key={i} className="w-1.5 h-1.5 rounded-full bg-slate-400"
                          style={{ animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite` }} />
                      ))}
                    </div>
                    <span className="text-xs text-slate-500">思考中...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
            <div className="flex gap-3 items-end">
              <textarea
                className="flex-1 rounded-xl px-4 py-3 text-sm resize-none outline-none transition-all"
                style={{
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  color: 'var(--text-primary)',
                  maxHeight: 120,
                  minHeight: 48,
                }}
                placeholder="输入问题，与智能体深度交流..."
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
                onFocus={e => e.target.style.borderColor = 'rgba(245,158,11,0.4)'}
                onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.08)'}
                rows={1}
              />
              <button
                onClick={handleSend}
                disabled={loading || !input.trim()}
                className="w-11 h-11 rounded-xl flex items-center justify-center transition-all flex-shrink-0"
                style={{
                  background: loading || !input.trim() ? 'rgba(245,158,11,0.2)' : 'linear-gradient(135deg, #f59e0b, #d97706)',
                  cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                }}
              >
                <Send size={16} style={{ color: loading || !input.trim() ? 'rgba(245,158,11,0.4)' : '#000' }} />
              </button>
            </div>
            <div className="text-xs text-slate-600 mt-2">Enter 发送 · Shift+Enter 换行</div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); }
          30% { transform: translateY(-6px); }
        }
      `}</style>
    </div>
  )
}
