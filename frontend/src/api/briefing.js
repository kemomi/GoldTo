import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 30000 })

export const listBriefings = (params = {}) =>
  api.get('/briefings', { params }).then(r => r.data)
export const getBriefing = (id) =>
  api.get(`/briefings/${id}`).then(r => r.data)
export const getBriefingEvents = (id) =>
  api.get(`/briefings/${id}/events`).then(r => r.data)
export const generateBriefingNow = () =>
  api.post('/briefings/generate').then(r => r.data)
export const getTodayBriefingStatus = () =>
  api.get('/briefings/today/status').then(r => r.data)

export const getSchedulerJobs = () =>
  api.get('/scheduler/jobs').then(r => r.data)
export const getDailyBriefingSchedule = () =>
  api.get('/scheduler/daily-briefing').then(r => r.data)
export const updateDailyBriefingSchedule = (data) =>
  api.post('/scheduler/daily-briefing', data).then(r => r.data)
export const runDailyBriefingNow = () =>
  api.post('/scheduler/daily-briefing/run-now').then(r => r.data)
export const stopDailyBriefing = () =>
  api.post('/scheduler/daily-briefing/stop').then(r => r.data)
