import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 30000 })

export const getDashboardOverview = () =>
  api.get('/dashboard/overview').then(r => r.data)

export const getDashboardTrends = (days = 30) =>
  api.get('/dashboard/trends', { params: { days } }).then(r => r.data)

export const getDashboardCategories = () =>
  api.get('/dashboard/categories').then(r => r.data)

export const getDashboardSources = () =>
  api.get('/dashboard/sources').then(r => r.data)

export const getHighRelevanceEvents = (params = {}) =>
  api.get('/dashboard/high-relevance', { params }).then(r => r.data)
