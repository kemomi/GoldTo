import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 30000 })

export const getSourcesStatus = () =>
  api.get('/sources/status').then(r => r.data)
export const getSourceConfig = () =>
  api.get('/sources/config').then(r => r.data)
export const updateSourceConfig = (data) =>
  api.post('/sources/config', data).then(r => r.data)
export const testSource = (sourceName) =>
  api.post(`/sources/test/${sourceName}`).then(r => r.data)
