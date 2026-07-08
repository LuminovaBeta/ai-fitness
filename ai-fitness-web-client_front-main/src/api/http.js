const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const buildHeaders = (auth = false, extraHeaders = {}) => {
  const headers = {
    'Content-Type': 'application/json',
    ...extraHeaders
  }

  if (auth) {
    const token = localStorage.getItem('auth_token')
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
  }

  return headers
}

export const request = async (path, options = {}) => {
  const { method = 'GET', body, auth = false, headers = {} } = options

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: buildHeaders(auth, headers),
    body: body ? JSON.stringify(body) : undefined
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const error = new Error(data.detail || data.msg || data.error || '请求失败')
    error.status = response.status
    error.data = data
    throw error
  }

  return data
}

export { API_BASE_URL }
