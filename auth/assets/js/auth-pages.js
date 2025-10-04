// Auth Pages Logic - Skreenit Edition
import { supabase, auth, db, storage } from './supabase-config.js'
import { backendFetch, backendUrl } from './backend-client.js'

// Resend integration note: use Resend on the server only. Do not expose API keys in the client.
function emailEnabled() {
  // Always false on client; email is sent by backend using Resend.
  return false
}

function initEmail() {
  // No-op. Backend endpoints should handle email via Resend.
  return
}

function showError(message) {
  const el = document.getElementById('formError')
  if (el) el.textContent = message
  else alert(message)
}

function generateTempPassword(length = 10) {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%^&*'
  return Array.from({ length }, () => chars[Math.floor(Math.random() * chars.length)]).join('')
}

function getFormValue(form, name) {
  const el = form.querySelector(`[name="${name}"]`)
  return el ? el.value.trim() : ''
}

function getFile(form, name) {
  const el = form.querySelector(`[name="${name}"]`)
  return el?.files?.[0] || null
}

function setLoading(btn, loading) {
  if (!btn) return
  btn.disabled = loading
  btn.textContent = loading ? 'Please wait...' : btn.dataset.originalText || 'Submit'
}

// ---- Registration ----
export async function handleRegistrationSubmit(e) {
  e.preventDefault()
  const form = e.currentTarget
  const submitBtn = form.querySelector('button[type="submit"]')
  setLoading(submitBtn, true)

  try {
    const full_name = getFormValue(form, 'full_name')
    const email = getFormValue(form, 'email')
    const mobile = getFormValue(form, 'mobile')
    const location = getFormValue(form, 'location')
    const role = getFormValue(form, 'role')
    const company_name = getFormValue(form, 'company_name')
    const resumeFile = getFile(form, 'resume')

    if (!full_name || !email || !mobile || !location || !role) {
      showError('Please fill all required fields')
      return
    }
    if (role === 'recruiter' && !company_name) {
      showError('Company Name is required for recruiter registration')
      return
    }

    const fd = new FormData()
    fd.append('full_name', full_name)
    fd.append('email', email)
    fd.append('mobile', mobile)
    fd.append('location', location)
    fd.append('role', role)
    if (company_name) fd.append('company_name', company_name)
    if (resumeFile) fd.append('resume', resumeFile)

    const host = window.location.hostname || ''
    const isLocal = host === 'localhost' || host === '127.0.0.1' || host === ''
    // Production API on onrender currently expects legacy keys: name, mobile_number
    if (!isLocal) {
      fd.append('name', full_name)
      fd.append('mobile_number', mobile)
    }
    const registerPath = isLocal ? '/auth/register' : '/register'
    const resp = await backendFetch(registerPath, { method: 'POST', body: fd })
    let out = {}
    const text = await resp.text()
    try { out = JSON.parse(text) } catch {}
    if (!resp.ok || out?.ok === false) {
      const url = backendUrl() + registerPath
      console.error('Registration POST failed', { url, status: resp.status, body: text })
      throw new Error(out?.error || `Registration failed (HTTP ${resp.status})`)
    }
    return true
  } catch (err) {
    console.error('Registration error:', err)
    showError(err.message || 'Registration failed')
    alert(`Registration failed: ${err.message || 'Unknown error'}`)
  } finally {
    setLoading(submitBtn, false)
  }
}

// ---- Login ----
export async function handleLoginSubmit(e) {
  e.preventDefault()
  const form = e.currentTarget
  const submitBtn = form.querySelector('button[type="submit"]')
  setLoading(submitBtn, true)

  try {
    const email = getFormValue(form, 'email')
    const password = getFormValue(form, 'password')
    const roleFromForm = getFormValue(form, 'role') || null
    const companyIdFromForm = getFormValue(form, 'company_id') || ''

    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw error

    const user = data.user
    const firstLogin = user?.user_metadata?.first_login === true
    let role = roleFromForm || user?.user_metadata?.role

    // Fallback: fetch role from public.users if not present in metadata
    if (!role) {
      try {
        const { data: roleRow } = await db
          .from('users')
          .select('role')
          .eq('id', user.id)
          .single()
        if (roleRow?.role) role = roleRow.role
      } catch {}
    }

    localStorage.setItem('skreenit_role', role)
    localStorage.setItem('skreenit_user_id', user.id)

    // Persist access token for backend Authorization headers (used by other pages)
    try {
      const { data: sessionData } = await supabase.auth.getSession()
      const token = sessionData?.session?.access_token
      if (token) localStorage.setItem('skreenit_token', token)
    } catch {}

    if (firstLogin) {
      // Pass session tokens across subdomain via URL hash for bootstrap
      let at = null, rt = null
      try {
        const { data: s } = await supabase.auth.getSession()
        at = s?.session?.access_token || null
        rt = s?.session?.refresh_token || null
      } catch {}
      const uid = user?.id || ''
      const r = role || ''
      const extras = `user_id=${encodeURIComponent(uid)}&role=${encodeURIComponent(r)}`
      const hash = (at && rt) ? `#access_token=${encodeURIComponent(at)}&refresh_token=${encodeURIComponent(rt)}&${extras}` : `#${extras}`
      window.location.href = `https://login.skreenit.com/update-password.html${hash}`
      return
    }

    function envRedirect(pathLocal, urlProd) {
      const host = window.location.hostname || ''
      const isLocal = host === 'localhost' || host === '127.0.0.1' || host === ''
      if (isLocal) return pathLocal
      return urlProd
    }

    if (role === 'candidate') {
      // Non-first-time candidate login: go to candidate dashboard with session tokens for bootstrap
      let at = null, rt = null
      try {
        const { data: s } = await supabase.auth.getSession()
        at = s?.session?.access_token || null
        rt = s?.session?.refresh_token || null
      } catch {}
      const uid = user?.id || ''
      const extras = `user_id=${encodeURIComponent(uid)}&role=candidate`
      const hash = (at && rt) ? `#access_token=${encodeURIComponent(at)}&refresh_token=${encodeURIComponent(rt)}&${extras}` : `#${extras}`
      window.location.href = envRedirect(`/dashboards/candidate-dashboard.html${hash}`, `https://dashboard.skreenit.com/candidate-dashboard.html${hash}`)
    } else if (role === 'recruiter') {
      // Validate company ID if provided/required
      // Ensure we have token for backend calls
      let at = null, rt = null
      try {
        const { data: s } = await supabase.auth.getSession()
        at = s?.session?.access_token || null
        rt = s?.session?.refresh_token || null
      } catch {}
      const token = at

      // Determine stored company_id (metadata or recruiter profile)
      let storedCompanyId = user?.user_metadata?.company_id || ''
      if (!storedCompanyId && token) {
        try {
          const resp = await backendFetch(`/recruiter/profile/${user.id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          })
          if (resp.ok) {
            const prof = await resp.json()
            storedCompanyId = prof?.profile?.company_id || ''
          }
        } catch {}
      }

      // If no stored company id, direct to recruiter profile to complete onboarding
      if (!storedCompanyId) {
        const extras = `user_id=${encodeURIComponent(user.id)}&role=recruiter`
        const hash = (at && rt) ? `#access_token=${encodeURIComponent(at)}&refresh_token=${encodeURIComponent(rt)}&${extras}` : `#${extras}`
        showError('Please complete your recruiter profile to get your Company ID.')
        window.location.href = `https://recruiter.skreenit.com/recruiter-profile.html${hash}`
        return
      }

      // Require company ID entry on form and validate
      if (!companyIdFromForm) {
        showError('Please enter your Company ID to login as Recruiter.')
        return
      }
      if (storedCompanyId && companyIdFromForm.trim().toUpperCase() !== storedCompanyId.trim().toUpperCase()) {
        showError('Company ID does not match your profile. Please check and try again.')
        return
      }

      const uid = user?.id || ''
      const extras = `user_id=${encodeURIComponent(uid)}&role=recruiter`
      const hash = (at && rt) ? `#access_token=${encodeURIComponent(at)}&refresh_token=${encodeURIComponent(rt)}&${extras}` : `#${extras}`
      window.location.href = envRedirect(`/dashboards/recruiter-dashboard.html${hash}`, `https://dashboard.skreenit.com/recruiter-dashboard.html${hash}`)
    } else {
      showError('Logged in, but role not set. Please contact support.')
    }
  } catch (err) {
    console.error('Login error:', err)
    showError(err.message || 'Login failed')
  } finally {
    setLoading(submitBtn, false)
  }
}

// ---- Update Password ----
export async function handleUpdatePasswordSubmit(e) {
  e.preventDefault()
  // initEmail removed: Resend is handled server-side.

  const form = e.currentTarget
  const submitBtn = form.querySelector('button[type="submit"]')
  setLoading(submitBtn, true)

  try {
    // Ensure we have a valid session when coming from Supabase redirect
    try {
      const hash = window.location.hash || ''
      const search = window.location.search || ''
      // Case 1: Password recovery link supplies access_token/refresh_token in hash
      if (hash.includes('access_token') && hash.includes('refresh_token')) {
        const params = new URLSearchParams(hash.replace(/^#/, ''))
        const access_token = params.get('access_token')
        const refresh_token = params.get('refresh_token')
        if (access_token && refresh_token) {
          const { error: setErr } = await supabase.auth.setSession({ access_token, refresh_token })
          if (setErr) throw setErr
        }
      // Case 2: Magic link/PKCE code flow (rare for this page) -> use exchangeCodeForSession
      } else if (search.includes('code=')) {
        const { error: exchErr } = await supabase.auth.exchangeCodeForSession(search)
        if (exchErr) throw exchErr
      }
    } catch (exErr) {
      console.warn('Session setup after redirect failed or not needed:', exErr)
    }

    const { data: sessionData } = await supabase.auth.getUser()
    const user = sessionData?.user
    if (!user) throw new Error('Not authenticated')

    const newPassword = getFormValue(form, 'new_password')
    const confirmPassword = getFormValue(form, 'confirm_password')

    if (!newPassword || newPassword.length < 8) {
      showError('Password must be at least 8 characters')
      return
    }
    if (newPassword !== confirmPassword) {
      showError('Passwords do not match')
      return
    }

    const { error: upErr } = await supabase.auth.updateUser({ password: newPassword })
    if (upErr) throw upErr

    try {
      await supabase.auth.updateUser({ data: { first_login: false } })
    } catch (metaErr) {
      console.warn('Metadata update failed (first_login=false):', metaErr)
    }

    // Show visible success message
    try {
      const successEl = document.getElementById('formError')
      if (successEl) {
        successEl.style.color = 'green'
        successEl.textContent = 'Password updated successfully. Redirecting...'
      }
    } catch {}

    // Persist token and determine role for redirect
    let role = null
    let currentUserId = ''
    try {
      const { data: sessionData } = await supabase.auth.getSession()
      const token = sessionData?.session?.access_token
      if (token) localStorage.setItem('skreenit_token', token)

      const { data: userData } = await supabase.auth.getUser()
      const updatedUser = userData?.user
      if (updatedUser) {
        currentUserId = updatedUser.id || ''
        localStorage.setItem('skreenit_user_id', currentUserId)
        role = updatedUser.user_metadata?.role || null
        if (!role) {
          try {
            const { data: roleRow } = await db
              .from('users')
              .select('role')
              .eq('id', currentUserId)
              .single()
            if (roleRow?.role) role = roleRow.role
          } catch {}
        }
        if (role) localStorage.setItem('skreenit_role', role)
      } else {
        // Fallback to any stored values
        currentUserId = localStorage.getItem('skreenit_user_id') || ''
        role = role || localStorage.getItem('skreenit_role') || null
      }
    } catch {}

    // Notify backend to send emails (password changed and recruiter company ID if applicable)
    try {
      const { data: sess } = await supabase.auth.getSession()
      const atNotify = sess?.session?.access_token
      if (atNotify) {
        await backendFetch('/auth/password-updated', { method: 'POST', headers: { 'Authorization': `Bearer ${atNotify}` } })
      }
    } catch {}

    // Redirect to login page to re-auth with the new password (env-aware)
    function envRedirect(pathLocal, urlProd) {
      const host = window.location.hostname || ''
      const isLocal = host === 'localhost' || host === '127.0.0.1' || host === ''
      return isLocal ? pathLocal : urlProd
    }
    window.location.href = envRedirect('/login/login.html', 'https://login.skreenit.com/login.html')
  } catch (err) {
    console.error('Update password error:', err)
    showError(err.message || 'Update failed')
  } finally {
    setLoading(submitBtn, false)
  }
}
