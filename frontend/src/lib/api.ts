import axios, { AxiosError, type AxiosRequestConfig } from 'axios'
import { apiConfigured, appConfig } from './env'
import { supabase } from './supabase'
import type { SuccessEnvelope } from './types'

export const api = axios.create({
  baseURL: appConfig.apiBaseUrl,
  timeout: 20_000,
  headers: { Accept: 'application/json' },
})

api.interceptors.request.use(async (config) => {
  if (!apiConfigured) throw new Error('Backend URL is not configured. Set VITE_API_BASE_URL.')
  if (supabase && !config.headers.Authorization) {
    const { data, error } = await supabase.auth.getSession()
    if (error) throw error
    const token = data.session?.access_token
    if (token) config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<{ error?: { code?: string } }>) => {
    const request = error.config as (AxiosRequestConfig & { _sessionHandled?: boolean }) | undefined
    if (error.response?.status === 401 && !request?._sessionHandled && supabase) {
      if (request) request._sessionHandled = true
      await supabase.auth.signOut({ scope: 'local' })
    }
    return Promise.reject(error)
  },
)

export async function getData<T>(path: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await api.get<SuccessEnvelope<T>>(path, config)
  return response.data.data
}

export async function postData<T, B>(path: string, body: B): Promise<T> {
  const response = await api.post<SuccessEnvelope<T>>(path, body)
  return response.data.data
}

export async function patchData<T, B>(path: string, body: B): Promise<T> {
  const response = await api.patch<SuccessEnvelope<T>>(path, body)
  return response.data.data
}

export async function deleteData<T>(path: string): Promise<T> {
  const response = await api.delete<SuccessEnvelope<T>>(path)
  return response.data.data
}

export function getApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const message = error.response?.data?.error?.message
    if (typeof message === 'string') return message
    if (!error.response) return 'Could not reach the backend. Check the API URL and server status.'
  }
  if (error instanceof Error) return error.message
  return 'Something went wrong. Please try again.'
}
