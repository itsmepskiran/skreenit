// auth/assets/js/backend-client.js

// A resilient backend client with environment-aware base URLs, timeout, and failover.
// Key features:
// - Env-based URLs: localhost for dev, configurable production backend via a global
// - Timeout using AbortController
// - Failover only on network errors or 5xx responses (not on 4xx like 422)
// - FormData-safe: does NOT set Content-Type when body is FormData
// - Convenience helpers: backendFetch/get/post/put/delete/uploadFile
// - handleResponse: consistent error parsing

class BackendClient {
  constructor() {
    this.backendUrls = this.getBackendUrls()
    this.currentUrlIndex = 0
    this.requestTimeout = 10000
    this.maxRetries = 3
  }

  getBackendUrls() {
    const host = window.location.hostname || ''
    const isLocal = host === 'localhost' || host === '127.0.0.1' || host === ''
    if (isLocal) {
      return ['http://localhost:8000']
    }
    // Production primary URL is configurable via a global injected variable
    // e.g. set window.__SKREENIT_BACKEND_URL__ = 'https://api.example.com' in your HTML
    const configured = (typeof window !== 'undefined' && window.__SKREENIT_BACKEND_URL__) ? window.__SKREENIT_BACKEND_URL__ : null
    if (configured) return [configured]
    // Fallback production host — using the existing `auth.skreenit.com` subdomain for API
    // Note: ensure your hosting platform routes API requests to the backend on this domain.
    return [
      'https://auth.skreenit.com'
    ]
  }

  getCurrentUrl() {
    return this.backendUrls[this.currentUrlIndex]
  }

  switchToNextUrl() {
    this.currentUrlIndex = (this.currentUrlIndex + 1) % this.backendUrls.length
    console.log(`Switched to backend URL: ${this.getCurrentUrl()}`)
  }

  // Internal fetch with timeout (AbortController)
  async fetchWithTimeout(url, options = {}, timeoutMs = 10000) {
    const controller = new AbortController()
    const id = setTimeout(() => controller.abort(), timeoutMs)
    try {
      const resp = await fetch(url, { ...options, signal: controller.signal })
      return resp
    } finally {
      clearTimeout(id)
    }
  }
  // Core request with retries and failover
  async request(endpoint, options = {}) {
    const { method = 'GET', body = null, headers = {}, timeout = this.requestTimeout } = options
    const token = localStorage.getItem('skreenit_token') || null

    const isFormData = (typeof FormData !== 'undefined') && body instanceof FormData
    const finalHeaders = { ...headers }
    if (!isFormData) {
      if (body && !finalHeaders['Content-Type']) finalHeaders['Content-Type'] = 'application/json'
    }
    if (token) finalHeaders['Authorization'] = `Bearer ${token}`

    const maxAttempts = Math.max(1, this.maxRetries)
    let lastError = null

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const baseUrl = this.getCurrentUrl()
      const url = `${baseUrl}${endpoint}`
      try {
        const resp = await this.fetchWithTimeout(url, {
          method,
          headers: finalHeaders,
          body: isFormData ? body : (body ? (typeof body === 'string' ? body : JSON.stringify(body)) : null),
          credentials: 'include',
        }, timeout)

        // Failover only on network errors or 5xx
        if (resp && resp.status >= 500) {
          this.switchToNextUrl()
          lastError = new Error(`Server error ${resp.status}`)
          continue
        }
        return resp
      } catch (err) {
        // Network/timeout error
        lastError = err
        this.switchToNextUrl()
        continue
      }
    }
    throw lastError || new Error('Request failed')
  }

  async get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' })
  }

  async post(endpoint, data = null, options = {}) {
    return this.request(endpoint, { ...options, method: 'POST', body: data })
  }

  async put(endpoint, data = null, options = {}) {
    return this.request(endpoint, { ...options, method: 'PUT', body: data })
  }

  async delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' })
  }

  // FormData upload helper (keeps Content-Type unset)
  async uploadFile(endpoint, formData, options = {}) {
    return this.request(endpoint, { method: 'POST', body: formData, ...options })
  }

  async healthCheck() {
    try {
      const response = await this.get('/health', { timeout: 5000 })
      return response.ok
    } catch (error) {
      console.warn(`Health check failed for ${this.getCurrentUrl()}: ${error.message}`)
      return false
    }
  }

  async getAllBackendStatus() {
    const status = {}
    for (let i = 0; i < this.backendUrls.length; i++) {
      const originalIndex = this.currentUrlIndex
      this.currentUrlIndex = i
      try {
        const isHealthy = await this.healthCheck()
        status[this.backendUrls[i]] = {
          healthy: isHealthy,
          responseTime: isHealthy ? 'OK' : 'FAILED'
        }
      } catch (error) {
        status[this.backendUrls[i]] = { healthy: false, error: error.message }
      }
      this.currentUrlIndex = originalIndex
    }
    return status
  }
}

// Global instance
const backendClient = new BackendClient()

// Convenience exports
export const backendFetch = async (endpoint, options = {}) => {
  return backendClient.request(endpoint, options)
}
export const backendGet = async (endpoint, options = {}) => {
  return backendClient.get(endpoint, options)
}
export const backendPost = async (endpoint, data = null, options = {}) => {
  return backendClient.post(endpoint, data, options)
}
export const backendPut = async (endpoint, data = null, options = {}) => {
  return backendClient.put(endpoint, data, options)
}
export const backendDelete = async (endpoint, options = {}) => {
  return backendClient.delete(endpoint, options)
}
export const backendUploadFile = async (endpoint, formData, options = {}) => {
  return backendClient.uploadFile(endpoint, formData, options)
}
export const backendUrl = () => backendClient.getCurrentUrl()
export const backendHealth = async () => backendClient.healthCheck()
export const backendStatus = async () => backendClient.getAllBackendStatus()

// Response helper used by callers to parse/throw consistently
export const handleResponse = async (response) => {
  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}`
    try {
      const errorData = await response.json()
      errorMessage = errorData.error || errorData.message || errorMessage
    } catch {
      errorMessage = response.statusText || errorMessage
    }
    throw new Error(errorMessage)
  }
  try {
    return await response.json()
  } catch {
    return await response.text()
  }
}
  export { backendClient }