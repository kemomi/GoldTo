export function downloadBlob(content, filename, type) {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export function markdownToWordHtml(markdown, title = '周大福海外市场战略简报') {
  const escapeHtml = str =>
    str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

  const lines = markdown.split('\n')
  const body = lines.map(line => {
    const escaped = escapeHtml(line)
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')

    if (line.startsWith('# ')) return `<h1>${escapeHtml(line.slice(2))}</h1>`
    if (line.startsWith('## ')) return `<h2>${escapeHtml(line.slice(3))}</h2>`
    if (line.startsWith('### ')) return `<h3>${escapeHtml(line.slice(4))}</h3>`
    if (line.startsWith('- ') || line.startsWith('* ')) return `<p class="li">• ${escaped.slice(2)}</p>`
    if (line.trim() === '') return '<p></p>'
    return `<p>${escaped}</p>`
  }).join('\n')

  return `<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>${escapeHtml(title)}</title>
  <style>
    body { font-family: "Microsoft YaHei", Arial, sans-serif; line-height: 1.65; color: #111827; }
    h1 { font-size: 24px; margin: 0 0 18px; }
    h2 { font-size: 18px; margin: 22px 0 8px; color: #92400e; }
    h3 { font-size: 15px; margin: 16px 0 6px; }
    p { font-size: 11pt; margin: 5px 0; }
    .li { margin-left: 18px; }
  </style>
</head>
<body>${body}</body>
</html>`
}

export function buildSessionMarkdown({ session, report, messages = [] }) {
  const chatLines = messages.map(m => {
    const speaker = m.role === 'user' ? '用户' : (m.agentName || 'Agent')
    return `### ${speaker}\n\n${m.content}`
  }).join('\n\n')

  return [
    `# 周大福海外市场战略情报归档`,
    '',
    `- 会话 ID：${session?.id || ''}`,
    `- 状态：${session?.status || ''}`,
    `- 情报任务：${session?.prediction_goal || ''}`,
    '',
    `## 战略简报`,
    '',
    report || session?.report || '暂无战略简报',
    '',
    `## 追问记录`,
    '',
    chatLines || '暂无追问记录',
  ].join('\n')
}
