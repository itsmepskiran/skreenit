// Centralized backend client with dual-URL failover
// Usage:
//   import { backendFetch, backendUrl } from './backend-client.js'
//   const res = await backendFetch('/path', { method: 'GET' })
//
// Configure at runtime via globals on each HTML page as needed:
//   window.SKREENIT_BACKEND_URLS = ['https://primary.example.com', 'https://secondary.example.com']
//   // or
//   window.SKREENIT_BACKEND_URL_PRIMARY = 'https://primary.example.com'
//   window.SKREENIT_BACKEND_URL_SECONDARY = 'https://secondary.example.com'
//
// If not provided, we fall back to a single legacy URL (no secondary).

function resolveBases() {
  const urls = Array.isArray(window.SKREENIT_BACKEND_URLS)
    ? window.SKREENIT_BACKEND_URLS.filter(Boolean)
    : []

  const primary = (window.SKREENIT_BACKEND_URL_PRIMARY || window.SKREENIT_BACKEND_URL || '').trim()
  const secondary = (window.SKREENIT_BACKEND_URL_SECONDARY || '').trim()

  const out = []
  if (urls.length) out.push(...urls)
  if (primary) out.push(primary)
  if (secondary) out.push(secondary)

  // Dedupe while preserving order
  const seen = new Set()
  const deduped = out.filter(u => {
    const key = (u || '').replace(/\/$/, '')
    if (!key || seen.has(key)) return false
    seen.add(key)
    return true
  })

  // Final fallback to legacy onrender if nothing configured
  if (!deduped.length) {
    deduped.push('https://skreenit-api.onrender.com')
  }

  return deduped.map(u => u.replace(/\/$/, ''))
}

function shouldFailover(status) {
  // Network errors already trigger failover by throwing. For HTTP responses:
  // Only failover on transient server-side errors.
  if (status >= 500) return true
  return false
}

export async function backendFetch(pathOrUrl, options = {}) {
  const bases = resolveBases()

  // If absolute URL passed, don't prepend base, but still we can try failover by replacing origin
  const isAbsolute = /^https?:\/\//i.test(pathOrUrl)

  let lastError = null

  for (let i = 0; i < bases.length; i++) {
    const base = bases[i]
    const url = isAbsolute
      ? pathOrUrl.replace(/^https?:\/\/[^/]+/, base)
      : base + (pathOrUrl.startsWith('/') ? pathOrUrl : '/' + pathOrUrl)

    try {
      const res = await fetch(url, options)
      if (res.ok) return res
      if (shouldFailover(res.status) && i < bases.length - 1) {
        continue
      }
      // Non-transient error: return as-is
      return res
    } catch (err) {
      lastError = err
      // Try next base
      if (i < bases.length - 1) continue
    }
  }

  // If we reach here, all attempts failed
  if (lastError) throw lastError
  throw new Error('All backend endpoints are unavailable')
}

export function backendUrl() {
  const bases = resolveBases()
  return bases[0]
}
