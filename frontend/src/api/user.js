import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 30000 })

export const getUserConfig = () => api.get('/user/config').then(r => r.data)
export const updateUserConfig = (data) => api.patch('/user/config', data).then(r => r.data)
export const updateChannelConfig = (data) => api.patch('/user/channels', data).then(r => r.data)
export const testPushChannel = (channel, title, content) =>
  api.post('/user/push-test', { channel, title, content }).then(r => r.data)
export const getPushChannels = () => api.get('/user/push-channels').then(r => r.data)
