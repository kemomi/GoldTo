import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 30000 })

export const getAlertRule = () =>
  api.get('/alert-rule').then(r => r.data)

export const saveAlertRule = (data) =>
  api.post('/alert-rule', data).then(r => r.data)

export const listAlerts = (params = {}) =>
  api.get('/alerts', { params }).then(r => r.data)

export const getAlertStats = () =>
  api.get('/alerts/stats').then(r => r.data)
