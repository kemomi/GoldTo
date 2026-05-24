import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// ── Sessions ──────────────────────────────────────────────────────────────────
export const createSession = () => api.post('/sessions').then(r => r.data)
export const getSession = id => api.get(`/sessions/${id}`).then(r => r.data)
export const listSessions = () => api.get('/sessions').then(r => r.data)

// ── Data Collection ───────────────────────────────────────────────────────────
export const collectData = (sessionId, topic) =>
  api.post(`/sessions/${sessionId}/collect`, { topic }).then(r => r.data)

export const uploadSeed = (sessionId, formData) =>
  api.post(`/sessions/${sessionId}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)

export const startAnalysis = sessionId =>
  api.post(`/sessions/${sessionId}/analyze`).then(r => r.data)

// ── Data ──────────────────────────────────────────────────────────────────────
export const getBriefing = sessionId =>
  api.get(`/sessions/${sessionId}/briefing`).then(r => r.data)

export const getEvents = sessionId =>
  api.get(`/sessions/${sessionId}/events`).then(r => r.data)

export const getHistory = (sessionId, params = {}) =>
  api.get(`/sessions/${sessionId}/history`, { params }).then(r => r.data).catch(() => ({ history: [], total: 0 }))

// ── Legacy compatibility (WorldPage) ──────────────────────────────────────────
export const getAgents = sessionId =>
  api.get(`/sessions/${sessionId}/agents`).then(r => r.data).catch(() => ({ agents: [] }))

export const getGraph = sessionId =>
  api.get(`/sessions/${sessionId}/graph`).then(r => r.data).catch(() => ({ graph: { nodes: [], edges: [] } }))

// ── Chat ──────────────────────────────────────────────────────────────────────
export const sendChat = (sessionId, message) =>
  api.post(`/sessions/${sessionId}/chat`, { message }).then(r => r.data)

// ── SSE Stream ────────────────────────────────────────────────────────────────
export const createEventSource = sessionId =>
  new EventSource(`/api/sessions/${sessionId}/stream`)

export default api
