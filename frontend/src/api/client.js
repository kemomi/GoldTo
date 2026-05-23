import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// ── Sessions ──────────────────────────────────────────────────────────────────
export const createSession = () => api.post('/sessions').then(r => r.data)
export const getSession = id => api.get(`/sessions/${id}`).then(r => r.data)
export const listSessions = () => api.get('/sessions').then(r => r.data)

// ── Upload & Simulate ─────────────────────────────────────────────────────────
export const uploadSeed = (sessionId, formData) =>
  api.post(`/sessions/${sessionId}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)

export const startSimulation = sessionId =>
  api.post(`/sessions/${sessionId}/simulate`).then(r => r.data)

// ── Data ──────────────────────────────────────────────────────────────────────
export const getReport = sessionId =>
  api.get(`/sessions/${sessionId}/report`).then(r => r.data)

export const getAgents = sessionId =>
  api.get(`/sessions/${sessionId}/agents`).then(r => r.data)

export const getGraph = sessionId =>
  api.get(`/sessions/${sessionId}/graph`).then(r => r.data)

export const getHistory = (sessionId, params = {}) =>
  api.get(`/sessions/${sessionId}/history`, { params }).then(r => r.data)

// ── Chat ──────────────────────────────────────────────────────────────────────
export const sendChat = (sessionId, message, agentId = null) =>
  api.post(`/sessions/${sessionId}/chat`, { message, agent_id: agentId }).then(r => r.data)

// ── SSE Stream ────────────────────────────────────────────────────────────────
export const createEventSource = sessionId =>
  new EventSource(`/api/sessions/${sessionId}/stream`)

export default api
