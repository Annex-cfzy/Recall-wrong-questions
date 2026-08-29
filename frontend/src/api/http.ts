import axios from 'axios'
import type { ApiResponse } from '@/types'
import { ElMessage } from 'element-plus'
import { messageForCode, UI_ERRORS } from '@/constants/errors'

// Axios instance — base path is proxied to the FastAPI backend in dev.
// In production (separated frontend/backend) you can set VITE_API_BASE to the
// backend origin (e.g. https://xxx.fc.aliyuncs.com); when unset it falls back
// to the same-origin "/api" path (used by the integrated deploy & dev proxy).
const apiBase = (import.meta.env.VITE_API_BASE as string | undefined) || '/api'
const http = axios.create({
  baseURL: apiBase,
  timeout: 60000,
})

// Unwrap the unified envelope: throw on business error code != 0.
http.interceptors.response.use(
  (resp) => {
    const body = resp.data as ApiResponse<unknown>
    if (body && typeof body.code === 'number' && body.code !== 0) {
      const msg = body.message || messageForCode(body.code)
      ElMessage.error(msg)
      return Promise.reject(new Error(msg))
    }
    return resp
  },
  (error) => {
    // Network / HTTP level errors.
    const msg =
      error?.response?.data?.message || error?.message || UI_ERRORS.NETWORK
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

export default http
