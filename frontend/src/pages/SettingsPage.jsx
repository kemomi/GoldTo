import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Settings, Mail, MessageSquare, Clock, Briefcase, Target,
  Users, Hash, ShoppingBag, BookOpen, AlertCircle, CheckCircle,
  Send, Bell, Globe, ChevronLeft, AlertTriangle
} from 'lucide-react'
import { getUserConfig, updateUserConfig, updateChannelConfig, testPushChannel, getPushChannels } from '../api/user'
import { getSourcesStatus, getSourceConfig, updateSourceConfig, testSource } from '../api/source'
import { getAlertRule, saveAlertRule } from '../api/alert'

export default function SettingsPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false) // false 或当前测试的渠道ID
  const [message, setMessage] = useState({ type: '', text: '' })
  const [channels, setChannels] = useState([])
  const [sources, setSources] = useState([])
  const [sourceMode, setSourceMode] = useState('mock')
  const [llmMode, setLlmMode] = useState('mock')
  const [llmModel, setLlmModel] = useState(null)
  const [testingSource, setTestingSource] = useState(null)
  const [sourceTestResult, setSourceTestResult] = useState(null)

  // 预警规则
  const [alertRule, setAlertRule] = useState({
    enabled: false,
    min_relevance: 0.85,
    keywords: [],
    categories: [],
    channels: [],
  })
  const [alertInputs, setAlertInputs] = useState({ keyword: '' })
  const [savingAlert, setSavingAlert] = useState(false)

  // 基础配置
  const [config, setConfig] = useState({
    nickname: '',
    email: '',
    industry: '',
    focus_targets: [],
    competitor_list: [],
    product_keywords: [],
    social_keywords: [],
    push_channels: [],
    push_time: '08:00',
    timezone: 'Asia/Shanghai',
    push_enabled: true,
    briefing_language: 'zh',
    briefing_detail_level: 'standard',
    briefing_sections: [],
  })

  // 渠道敏感配置
  const [channelConfig, setChannelConfig] = useState({
    email_smtp_host: '',
    email_smtp_port: 587,
    email_smtp_user: '',
    email_smtp_pass: '',
    email_sender: '',
    feishu_webhook: '',
    feishu_app_id: '',
    feishu_app_secret: '',
    wecom_webhook: '',
    dingtalk_webhook: '',
  })

  // 临时输入框
  const [inputs, setInputs] = useState({
    focus_target: '',
    competitor: '',
    product_keyword: '',
    social_keyword: '',
  })

  useEffect(() => {
    Promise.all([getUserConfig(), getPushChannels(), getSourceConfig(), getSourcesStatus()]).then(([cfg, ch, srcCfg, srcStatus]) => {
      if (cfg.id) {
        setConfig(prev => ({ ...prev, ...cfg }))
        // 同步渠道配置到 channelConfig state
        setChannelConfig(prev => ({
          ...prev,
          email_smtp_host: cfg.email_smtp_host || '',
          email_smtp_port: cfg.email_smtp_port || 587,
          email_smtp_user: cfg.email_smtp_user || '',
          email_sender: cfg.email_sender || '',
          feishu_webhook: cfg.feishu_webhook || '',
          feishu_app_id: cfg.feishu_app_id || '',
          wecom_webhook: cfg.wecom_webhook || '',
          dingtalk_webhook: cfg.dingtalk_webhook || '',
        }))
      }
      setChannels(ch.channels || [])
      // 同步数据源模式
      if (srcCfg) {
        setSourceMode(srcCfg.enable_real_sources ? 'real' : 'mock')
        setLlmMode(srcCfg.llm_mode || 'mock')
        setLlmModel(srcCfg.llm_model || null)
      }
      if (srcStatus) {
        setSources(srcStatus.sources || [])
      }
      // 加载预警规则
      return getAlertRule()
    }).then(alertRes => {
      if (alertRes.success && alertRes.data) {
        setAlertRule(prev => ({ ...prev, ...alertRes.data }))
      }
      setLoading(false)
    }).catch(err => {
      setMessage({ type: 'error', text: '加载配置失败' })
      setLoading(false)
    })
  }, [])

  const showMsg = (type, text) => {
    setMessage({ type, text })
    setTimeout(() => setMessage({ type: '', text: '' }), 3000)
  }

  const handleSave = async () => {
    // 基础验证
    if (config.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(config.email)) {
      showMsg('error', '邮箱格式不正确')
      return
    }
    if (!/^([01]\d|2[0-3]):([0-5]\d)$/.test(config.push_time)) {
      showMsg('error', '推送时间格式应为 HH:MM')
      return
    }
    setSaving(true)
    try {
      await updateUserConfig(config)
      await updateChannelConfig(channelConfig)
      showMsg('success', '配置已保存')
      // 重新拉取最新配置
      const fresh = await getUserConfig()
      if (fresh.id) {
        setConfig(prev => ({ ...prev, ...fresh }))
        setChannelConfig(prev => ({
          ...prev,
          email_smtp_host: fresh.email_smtp_host || '',
          email_smtp_port: fresh.email_smtp_port || 587,
          email_smtp_user: fresh.email_smtp_user || '',
          email_sender: fresh.email_sender || '',
          feishu_webhook: fresh.feishu_webhook || '',
          feishu_app_id: fresh.feishu_app_id || '',
          wecom_webhook: fresh.wecom_webhook || '',
          dingtalk_webhook: fresh.dingtalk_webhook || '',
        }))
      }
    } catch (e) {
      showMsg('error', e.response?.data?.detail || '保存失败')
    }
    setSaving(false)
  }

  const handleTestPush = async (channel) => {
    setTesting(channel)
    try {
      const res = await testPushChannel(channel, 'GoldTo 推送测试', '这是一条测试消息，验证推送渠道配置是否正确。')
      showMsg(res.success ? 'success' : 'error', res.message)
    } catch (e) {
      showMsg('error', e.response?.data?.detail || '测试失败')
    }
    setTesting(false)
  }

  const handleToggleSourceMode = async () => {
    const newMode = sourceMode === 'mock' ? 'real' : 'mock'
    try {
      await updateSourceConfig({ enable_real_sources: newMode === 'real' })
      setSourceMode(newMode)
      showMsg('success', `已切换到 ${newMode === 'real' ? '真实数据源' : 'Mock 数据'} 模式`)
      // 刷新数据源状态
      const src = await getSourcesStatus()
      setSources(src.sources || [])
    } catch (e) {
      showMsg('error', '切换数据源模式失败')
    }
  }

  const handleTestSource = async (sourceName) => {
    setTestingSource(sourceName)
    setSourceTestResult(null)
    try {
      const res = await testSource(sourceName)
      setSourceTestResult(res)
    } catch (e) {
      showMsg('error', '数据源测试失败')
    }
    setTestingSource(null)
  }

  const addItem = (field, inputKey) => {
    const val = inputs[inputKey].trim()
    if (!val) return
    setConfig(prev => ({
      ...prev,
      [field]: [...(prev[field] || []), val]
    }))
    setInputs(prev => ({ ...prev, [inputKey]: '' }))
  }

  const removeItem = (field, idx) => {
    setConfig(prev => ({
      ...prev,
      [field]: prev[field].filter((_, i) => i !== idx)
    }))
  }

  // ── Alert Rule handlers ──

  const handleSaveAlert = async () => {
    setSavingAlert(true)
    try {
      const res = await saveAlertRule(alertRule)
      if (res.success) {
        showMsg('success', '预警规则已保存')
        setAlertRule(prev => ({ ...prev, ...res.data }))
      }
    } catch (e) {
      showMsg('error', '保存预警规则失败')
    }
    setSavingAlert(false)
  }

  const addAlertKeyword = () => {
    const val = alertInputs.keyword.trim()
    if (!val) return
    if (alertRule.keywords.includes(val)) return
    setAlertRule(prev => ({ ...prev, keywords: [...prev.keywords, val] }))
    setAlertInputs(prev => ({ ...prev, keyword: '' }))
  }

  const removeAlertKeyword = (idx) => {
    setAlertRule(prev => ({
      ...prev,
      keywords: prev.keywords.filter((_, i) => i !== idx)
    }))
  }

  const toggleAlertCategory = (cat) => {
    setAlertRule(prev => ({
      ...prev,
      categories: prev.categories.includes(cat)
        ? prev.categories.filter(c => c !== cat)
        : [...prev.categories, cat]
    }))
  }

  const toggleAlertChannel = (ch) => {
    setAlertRule(prev => ({
      ...prev,
      channels: prev.channels.includes(ch)
        ? prev.channels.filter(c => c !== ch)
        : [...prev.channels, ch]
    }))
  }

  if (loading) {
    return (
      <div className="min-h-full flex items-center justify-center">
        <div className="spinner w-6 h-6" />
      </div>
    )
  }

  return (
    <div className="min-h-full p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <button onClick={() => navigate(-1)} className="p-2 rounded-lg hover:bg-white/5 transition-colors">
          <ChevronLeft size={20} className="text-slate-400" />
        </button>
        <Settings size={24} className="text-amber-400" />
        <div>
          <h1 className="text-2xl font-bold text-white">系统配置</h1>
          <p className="text-slate-500 text-sm">配置行业、关注目标和推送渠道</p>
        </div>
      </div>

      {message.text && (
        <div className={`mb-6 flex items-center gap-2 text-sm p-3 rounded-lg ${
          message.type === 'success'
            ? 'bg-green-500/10 border border-green-500/20 text-green-400'
            : 'bg-red-500/10 border border-red-500/20 text-red-400'
        }`}>
          {message.type === 'success' ? <CheckCircle size={15} /> : <AlertCircle size={15} />}
          {message.text}
        </div>
      )}

      <div className="space-y-6">
        {/* 基础信息 */}
        <Section icon={<Briefcase size={18} />} title="基础信息">
          <div className="grid grid-cols-2 gap-4">
            <Input label="昵称" value={config.nickname} onChange={v => setConfig(p => ({ ...p, nickname: v }))} />
            <Input label="邮箱" value={config.email} onChange={v => setConfig(p => ({ ...p, email: v }))} />
            <Input label="所在行业" value={config.industry} onChange={v => setConfig(p => ({ ...p, industry: v }))} placeholder="例如：新能源汽车、SaaS、消费品" />
            <Input label="推送时间" type="time" value={config.push_time} onChange={v => setConfig(p => ({ ...p, push_time: v }))} />
          </div>
          <div className="mt-4 flex items-center gap-3">
            <input
              type="checkbox"
              checked={config.push_enabled}
              onChange={e => setConfig(p => ({ ...p, push_enabled: e.target.checked }))}
              className="w-4 h-4 accent-amber-500"
            />
            <span className="text-sm text-slate-300">启用每日战略简报推送</span>
          </div>
        </Section>

        {/* 关注目标 */}
        <Section icon={<Target size={18} />} title="关注目标">
          <TagInput
            label="战略关注点"
            placeholder="输入后回车添加，如：中东局势、AI监管..."
            tags={config.focus_targets}
            inputValue={inputs.focus_target}
            onInputChange={v => setInputs(p => ({ ...p, focus_target: v }))}
            onAdd={() => addItem('focus_targets', 'focus_target')}
            onRemove={idx => removeItem('focus_targets', idx)}
          />
        </Section>

        {/* 竞争对手 */}
        <Section icon={<Users size={18} />} title="竞争对手监测">
          <TagInput
            label="竞争对手名单"
            placeholder="输入竞争对手名称..."
            tags={config.competitor_list}
            inputValue={inputs.competitor}
            onInputChange={v => setInputs(p => ({ ...p, competitor: v }))}
            onAdd={() => addItem('competitor_list', 'competitor')}
            onRemove={idx => removeItem('competitor_list', idx)}
          />
        </Section>

        {/* 产品关键词 */}
        <Section icon={<ShoppingBag size={18} />} title="产品与趋势">
          <div className="space-y-3">
            <TagInput
              label="产品关键词"
              placeholder="输入产品或品类关键词..."
              tags={config.product_keywords}
              inputValue={inputs.product_keyword}
              onInputChange={v => setInputs(p => ({ ...p, product_keyword: v }))}
              onAdd={() => addItem('product_keywords', 'product_keyword')}
              onRemove={idx => removeItem('product_keywords', idx)}
            />
            <TagInput
              label="社交媒体监测词"
              placeholder="输入社交媒体监测关键词..."
              tags={config.social_keywords}
              inputValue={inputs.social_keyword}
              onInputChange={v => setInputs(p => ({ ...p, social_keyword: v }))}
              onAdd={() => addItem('social_keywords', 'social_keyword')}
              onRemove={idx => removeItem('social_keywords', idx)}
            />
          </div>
        </Section>

        {/* 推送渠道 */}
        <Section icon={<Bell size={18} />} title="推送渠道">
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              {channels.map(ch => (
                <button
                  key={ch.id}
                  onClick={() => {
                    const has = config.push_channels.includes(ch.id)
                    setConfig(p => ({
                      ...p,
                      push_channels: has
                        ? p.push_channels.filter(c => c !== ch.id)
                        : [...p.push_channels, ch.id]
                    }))
                  }}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${
                    config.push_channels.includes(ch.id)
                      ? 'border-amber-500/40 bg-amber-500/10 text-amber-400'
                      : 'border-white/10 text-slate-500 hover:border-white/20'
                  } ${!ch.configurable ? 'opacity-50 cursor-not-allowed' : ''}`}
                  disabled={!ch.configurable}
                >
                  {ch.name} {!ch.configurable && '(预留)'}
                </button>
              ))}
            </div>

            {/* 邮件配置 */}
            {config.push_channels.includes('email') && (
              <div className="p-4 rounded-lg border border-white/5 bg-white/[0.02] space-y-3">
                <div className="flex items-center gap-2 text-sm font-medium text-slate-300">
                  <Mail size={14} className="text-amber-400" /> SMTP 配置
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <Input label="SMTP 服务器" value={channelConfig.email_smtp_host} onChange={v => setChannelConfig(p => ({ ...p, email_smtp_host: v }))} placeholder="smtp.example.com" />
                  <Input label="端口" type="number" value={channelConfig.email_smtp_port} onChange={v => setChannelConfig(p => ({ ...p, email_smtp_port: parseInt(v) || 587 }))} />
                  <Input label="用户名" value={channelConfig.email_smtp_user} onChange={v => setChannelConfig(p => ({ ...p, email_smtp_user: v }))} />
                  <Input label="密码" type="password" value={channelConfig.email_smtp_pass} onChange={v => setChannelConfig(p => ({ ...p, email_smtp_pass: v }))} />
                  <Input label="发件人" value={channelConfig.email_sender} onChange={v => setChannelConfig(p => ({ ...p, email_sender: v }))} placeholder="goldto@example.com" />
                </div>
                <button
                  onClick={() => handleTestPush('email')}
                  disabled={testing}
                  className="text-xs px-3 py-1.5 rounded-lg border border-amber-500/30 text-amber-400 hover:bg-amber-500/10 transition-all flex items-center gap-1 disabled:opacity-50"
                >
                  <Send size={12} /> {testing === 'email' ? '发送中...' : '测试邮件'}
                </button>
              </div>
            )}

            {/* 飞书配置 */}
            {config.push_channels.includes('feishu') && (
              <div className="p-4 rounded-lg border border-white/5 bg-white/[0.02] space-y-3">
                <div className="flex items-center gap-2 text-sm font-medium text-slate-300">
                  <MessageSquare size={14} className="text-amber-400" /> 飞书配置
                </div>
                <Input label="Webhook URL" value={channelConfig.feishu_webhook} onChange={v => setChannelConfig(p => ({ ...p, feishu_webhook: v }))} placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/..." />
                <div className="grid grid-cols-2 gap-3">
                  <Input label="App ID (可选)" value={channelConfig.feishu_app_id} onChange={v => setChannelConfig(p => ({ ...p, feishu_app_id: v }))} />
                  <Input label="App Secret (可选)" type="password" value={channelConfig.feishu_app_secret} onChange={v => setChannelConfig(p => ({ ...p, feishu_app_secret: v }))} />
                </div>
                <button
                  onClick={() => handleTestPush('feishu')}
                  disabled={testing}
                  className="text-xs px-3 py-1.5 rounded-lg border border-amber-500/30 text-amber-400 hover:bg-amber-500/10 transition-all flex items-center gap-1 disabled:opacity-50"
                >
                  <Send size={12} /> {testing === 'feishu' ? '发送中...' : '测试飞书'}
                </button>
              </div>
            )}

            {/* 企业微信配置 */}
            {config.push_channels.includes('wecom') && (
              <div className="p-4 rounded-lg border border-white/5 bg-white/[0.02] space-y-3">
                <div className="flex items-center gap-2 text-sm font-medium text-slate-300">
                  <Globe size={14} className="text-amber-400" /> 企业微信配置
                </div>
                <Input label="Webhook URL" value={channelConfig.wecom_webhook} onChange={v => setChannelConfig(p => ({ ...p, wecom_webhook: v }))} placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..." />
                <div className="text-[11px] text-slate-600">
                  在群聊中添加「群机器人」，复制 Webhook 地址填入此处
                </div>
                <button
                  onClick={() => handleTestPush('wecom')}
                  disabled={testing}
                  className="text-xs px-3 py-1.5 rounded-lg border border-amber-500/30 text-amber-400 hover:bg-amber-500/10 transition-all flex items-center gap-1 disabled:opacity-50"
                >
                  <Send size={12} /> {testing === 'wecom' ? '发送中...' : '测试企业微信'}
                </button>
              </div>
            )}

            {/* 钉钉配置 */}
            {config.push_channels.includes('dingtalk') && (
              <div className="p-4 rounded-lg border border-white/5 bg-white/[0.02] space-y-3">
                <div className="flex items-center gap-2 text-sm font-medium text-slate-300">
                  <Bell size={14} className="text-amber-400" /> 钉钉配置
                </div>
                <Input label="Webhook URL" value={channelConfig.dingtalk_webhook} onChange={v => setChannelConfig(p => ({ ...p, dingtalk_webhook: v }))} placeholder="https://oapi.dingtalk.com/robot/send?access_token=..." />
                <div className="text-[11px] text-slate-600">
                  在群设置中添加「智能群助手」→「机器人」，选择「自定义」，复制 Webhook 地址填入此处
                </div>
                <button
                  onClick={() => handleTestPush('dingtalk')}
                  disabled={testing}
                  className="text-xs px-3 py-1.5 rounded-lg border border-amber-500/30 text-amber-400 hover:bg-amber-500/10 transition-all flex items-center gap-1 disabled:opacity-50"
                >
                  <Send size={12} /> {testing === 'dingtalk' ? '发送中...' : '测试钉钉'}
                </button>
              </div>
            )}
          </div>
        </Section>

        {/* 数据源配置 */}
        <Section icon={<Globe size={18} />} title="数据源配置">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-sm font-medium text-slate-300">数据采集模式</div>
              <div className="text-xs text-slate-500 mt-0.5">
                {sourceMode === 'real'
                  ? '使用 RSS / Reddit / Hacker News 等真实数据源'
                  : '使用模拟数据（无需网络，用于演示）'}
              </div>
              <div className="text-[10px] mt-1 flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${llmMode === 'real' ? 'bg-green-400' : 'bg-amber-400'}`} />
                <span className={llmMode === 'real' ? 'text-green-400' : 'text-amber-400'}>
                  简报生成：{llmMode === 'real' ? `Kimi 真实模型${llmModel ? ` (${llmModel})` : ''}` : 'Mock 模板（未配置 API Key）'}
                </span>
              </div>
            </div>
            <button
              onClick={handleToggleSourceMode}
              className={`px-4 py-2 rounded-lg text-xs font-medium border transition-all ${
                sourceMode === 'real'
                  ? 'border-green-500/30 bg-green-500/10 text-green-400'
                  : 'border-amber-500/30 bg-amber-500/10 text-amber-400'
              }`}
            >
              {sourceMode === 'real' ? '✓ 真实数据源' : 'Mock 模式'}
            </button>
          </div>

          <div className="space-y-2">
            {sources.map(src => (
              <div key={src.name} className="flex items-center justify-between p-3 rounded-lg"
                style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)' }}>
                <div className="flex items-center gap-3">
                  <span className={`w-2 h-2 rounded-full ${src.available ? 'bg-green-400' : 'bg-red-400'}`} />
                  <div>
                    <div className="text-xs font-medium text-slate-300">{src.category}</div>
                    <div className="text-[10px] text-slate-500">{src.message}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] px-2 py-0.5 rounded ${
                    src.mode === 'real'
                      ? 'bg-green-500/10 text-green-400'
                      : 'bg-slate-500/10 text-slate-400'
                  }`}>
                    {src.mode === 'real' ? '真实' : 'Mock'}
                  </span>
                  <button
                    onClick={() => handleTestSource(src.name)}
                    disabled={testingSource === src.name}
                    className="text-[10px] px-2 py-1 rounded border border-amber-500/30 text-amber-400 hover:bg-amber-500/10 transition-all disabled:opacity-50"
                  >
                    {testingSource === src.name ? '测试中...' : '测试'}
                  </button>
                </div>
              </div>
            ))}
          </div>

          {sourceTestResult && (
            <div className="mt-3 p-3 rounded-lg" style={{ background: 'rgba(245,158,11,0.05)', border: '1px solid rgba(245,158,11,0.15)' }}>
              <div className="text-xs font-medium text-amber-400 mb-2">
                {sourceTestResult.source} 测试结果（{sourceTestResult.mode}）
              </div>
              {sourceTestResult.error ? (
                <div className="text-xs text-red-400">{sourceTestResult.error}</div>
              ) : (
                <div className="space-y-1.5">
                  {sourceTestResult.events?.map((ev, i) => (
                    <div key={i} className="text-xs text-slate-300">
                      <span className="text-amber-400/60">{ev.source}</span> · {ev.title}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </Section>

        {/* 情报预警规则 */}
        <Section icon={<AlertTriangle size={18} />} title="情报预警规则">
          <div className="flex items-center justify-between mb-5">
            <div>
              <div className="text-sm font-medium text-slate-300">实时情报预警</div>
              <div className="text-xs text-slate-500 mt-0.5">
                {alertRule.enabled
                  ? '当事件满足条件时，立即通过配置的渠道推送告警'
                  : '关闭中，每日简报生成时不会触发即时告警'}
              </div>
            </div>
            <button
              onClick={() => setAlertRule(prev => ({ ...prev, enabled: !prev.enabled }))}
              className={`px-4 py-2 rounded-lg text-xs font-medium border transition-all ${
                alertRule.enabled
                  ? 'border-green-500/30 bg-green-500/10 text-green-400'
                  : 'border-slate-500/30 bg-slate-500/10 text-slate-400'
              }`}
            >
              {alertRule.enabled ? '✓ 已启用' : '已关闭'}
            </button>
          </div>

          {alertRule.enabled && (
            <div className="space-y-5">
              {/* 相关度阈值 */}
              <div>
                <label className="block text-xs text-slate-500 mb-2">
                  相关度阈值: {(alertRule.min_relevance * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="1"
                  step="0.05"
                  value={alertRule.min_relevance}
                  onChange={e => setAlertRule(prev => ({ ...prev, min_relevance: parseFloat(e.target.value) }))}
                  className="w-full accent-amber-500"
                />
                <div className="flex justify-between text-[10px] text-slate-600 mt-0.5">
                  <span>50%</span>
                  <span>75%</span>
                  <span>100%</span>
                </div>
              </div>

              {/* 关键词 */}
              <div>
                <label className="block text-xs text-slate-500 mb-2">监控关键词（标题或摘要命中即触发）</label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {alertRule.keywords.map((kw, i) => (
                    <span key={i} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs"
                      style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.2)', color: '#60a5fa' }}>
                      {kw}
                      <button onClick={() => removeAlertKeyword(i)} className="hover:text-white">&times;</button>
                    </span>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={alertInputs.keyword}
                    onChange={e => setAlertInputs(prev => ({ ...prev, keyword: e.target.value }))}
                    onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addAlertKeyword())}
                    placeholder="输入关键词，回车添加"
                    className="flex-1 rounded-lg px-3 py-2 text-sm outline-none transition-all"
                    style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--text-primary)' }}
                  />
                  <button
                    onClick={addAlertKeyword}
                    className="px-3 py-2 rounded-lg text-xs font-medium text-blue-400 border border-blue-500/30 hover:bg-blue-500/10 transition-all"
                  >
                    添加
                  </button>
                </div>
              </div>

              {/* 监控类别 */}
              <div>
                <label className="block text-xs text-slate-500 mb-2">监控类别（不选则监控全部）</label>
                <div className="flex flex-wrap gap-2">
                  {[
                    { value: 'geopolitics', label: '地缘政治' },
                    { value: 'market', label: '市场动态' },
                    { value: 'policy', label: '政策监管' },
                    { value: 'competitor', label: '竞争对手' },
                    { value: 'social', label: '社交媒体' },
                    { value: 'product', label: '产品趋势' },
                    { value: 'legal', label: '法律合规' },
                    { value: 'tech', label: '科技创新' },
                    { value: 'energy', label: '能源' },
                  ].map(cat => (
                    <button
                      key={cat.value}
                      onClick={() => toggleAlertCategory(cat.value)}
                      className={`px-2.5 py-1 rounded-lg text-[11px] font-medium border transition-all ${
                        alertRule.categories.includes(cat.value)
                          ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                          : 'bg-white/[0.02] text-slate-500 border-white/5 hover:border-white/10'
                      }`}
                    >
                      {alertRule.categories.includes(cat.value) ? '✓ ' : ''}{cat.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* 推送渠道 */}
              <div>
                <label className="block text-xs text-slate-500 mb-2">告警推送渠道</label>
                <div className="flex gap-3 flex-wrap">
                  {[
                    { id: 'email', label: 'Email 邮件', icon: Mail },
                    { id: 'feishu', label: '飞书 Webhook', icon: MessageSquare },
                    { id: 'wecom', label: '企业微信', icon: Globe },
                    { id: 'dingtalk', label: '钉钉', icon: Bell },
                  ].map(ch => {
                    const Icon = ch.icon
                    const configured = (() => {
                      if (ch.id === 'email') return !!(channelConfig.email_smtp_host && channelConfig.email_smtp_user)
                      if (ch.id === 'feishu') return !!channelConfig.feishu_webhook
                      if (ch.id === 'wecom') return !!channelConfig.wecom_webhook
                      if (ch.id === 'dingtalk') return !!channelConfig.dingtalk_webhook
                      return false
                    })()
                    return (
                      <button
                        key={ch.id}
                        onClick={() => configured && toggleAlertChannel(ch.id)}
                        disabled={!configured}
                        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium border transition-all ${
                          alertRule.channels.includes(ch.id)
                            ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                            : configured
                              ? 'bg-white/[0.02] text-slate-400 border-white/5 hover:border-white/10'
                              : 'bg-white/[0.02] text-slate-600 border-white/5 cursor-not-allowed opacity-50'
                        }`}
                      >
                        <Icon size={12} />
                        {ch.label}
                        {!configured && <span className="text-[9px] text-slate-600">(未配置)</span>}
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* 保存预警规则按钮 */}
              <div className="flex justify-end pt-2">
                <button
                  onClick={handleSaveAlert}
                  disabled={savingAlert}
                  className="px-5 py-2 rounded-xl text-sm font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20 hover:bg-blue-500/20 transition-all disabled:opacity-50"
                >
                  {savingAlert ? '保存中...' : '保存预警规则'}
                </button>
              </div>
            </div>
          )}
        </Section>

        {/* 保存按钮 */}
        <div className="flex justify-end pt-4">
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-6 py-2.5 rounded-xl font-semibold text-sm transition-all"
            style={{
              background: saving ? 'rgba(245,158,11,0.3)' : 'linear-gradient(135deg, #f59e0b, #d97706)',
              color: '#000',
              cursor: saving ? 'not-allowed' : 'pointer',
            }}
          >
            {saving ? '保存中...' : '保存配置'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Sub-components ──

function Section({ icon, title, children }) {
  return (
    <div className="rounded-xl p-6" style={{ background: 'var(--dark-800)', border: '1px solid rgba(255,255,255,0.06)' }}>
      <div className="flex items-center gap-2 text-sm font-semibold text-slate-300 mb-4">
        {icon} {title}
      </div>
      {children}
    </div>
  )
}

function Input({ label, type = 'text', value, onChange, placeholder }) {
  return (
    <div>
      <label className="block text-xs text-slate-500 mb-1.5">{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg px-3 py-2 text-sm outline-none transition-all"
        style={{
          background: 'rgba(255,255,255,0.04)',
          border: '1px solid rgba(255,255,255,0.08)',
          color: 'var(--text-primary)',
        }}
      />
    </div>
  )
}

function TagInput({ label, placeholder, tags, inputValue, onInputChange, onAdd, onRemove }) {
  return (
    <div>
      <label className="block text-xs text-slate-500 mb-1.5">{label}</label>
      <div className="flex flex-wrap gap-2 mb-2">
        {tags.map((tag, i) => (
          <span key={i} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs"
            style={{ background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)', color: '#fbbf24' }}>
            {tag}
            <button onClick={() => onRemove(i)} className="hover:text-white">&times;</button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          value={inputValue}
          onChange={e => onInputChange(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), onAdd())}
          placeholder={placeholder}
          className="flex-1 rounded-lg px-3 py-2 text-sm outline-none transition-all"
          style={{
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.08)',
            color: 'var(--text-primary)',
          }}
        />
        <button
          onClick={onAdd}
          className="px-3 py-2 rounded-lg text-xs font-medium text-amber-400 border border-amber-500/30 hover:bg-amber-500/10 transition-all"
        >
          添加
        </button>
      </div>
    </div>
  )
}
