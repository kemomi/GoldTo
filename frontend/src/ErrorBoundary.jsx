import React from 'react'

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    console.error('React Error:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 40, color: '#f87171', fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
          <h2>页面渲染出错</h2>
          <p>{this.state.error?.toString?.() || 'Unknown error'}</p>
          <p style={{ color: '#94a3b8', marginTop: 20 }}>
            请刷新页面重试，或检查控制台日志。
          </p>
        </div>
      )
    }
    return this.props.children
  }
}
