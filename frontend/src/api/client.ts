import axios from 'axios'
import { message } from 'antd'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('[Axios] Request:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('[Axios] Request error:', error)
    return Promise.reject(error)
  },
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('[Axios] Response:', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('[Axios] Response error:', error.response?.status, error.config?.url, error.message)
    const msg =
      error.response?.data?.detail || error.response?.data?.message || error.message || '请求失败'
    message.error(msg)
    return Promise.reject(error)
  },
)

export default api
