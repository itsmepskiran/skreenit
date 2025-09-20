// Auth Pages Logic - Skreenit Edition
import { supabase, auth, db, storage } from './supabase-config.js'

// ---- EmailJS Config (Optional) ----
const EMAILJS_SERVICE_ID = 'YOUR_EMAILJS_SERVICE_ID'
const EMAILJS_TEMPLATE_ID_REG = 'YOUR_EMAILJS_TEMPLATE_ID_REG'
const EMAILJS_TEMPLATE_ID_PW = 'YOUR_EMAILJS_TEMPLATE_ID_PW'
const EMAILJS_PUBLIC_KEY = 'YOUR_EMAILJS_PUBLIC_KEY'

function emailEnabled() {
  return (
    typeof window !== 'undefined' &&
    window.emailjs &&
    EMAILJS_SERVICE_ID !== 'YOUR_EMAILJS_SERVICE_ID' &&
    EMAILJS_PUBLIC_KEY !== 'YOUR_EMAILJS_PUBLIC_KEY'
  )
}

function initEmail() {
  try {
    if (emailEnabled()) window.emailjs.init(EMAILJS_PUBLIC_KEY)
  } catch (e) {
    console.warn('EmailJS init skipped:', e)
  }
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
  initEmail()

  const form = e.currentTarget
  const submitBtn = form.querySelector('button[type="submit"]')
  setLoading(submitBtn, true)

  try {
    const full_name = getFormValue(form, 'full_name')
    const email = getFormValue(form, 'email')
    const mobile = getFormValue(form, 'mobile')
    const location = getFormValue(form, 'location')
    const role = getFormValue(form, 'role')
    const company_id = getFormValue(form, 'company_id')
    const resumeFile = getFile(form, 'resume')

    if (!full_name || !email || !mobile || !location || !role) {
      showError('Please fill all required fields')
      return
    }
    if (role === 'recruiter' && !company_id) {
      showError('Company ID is required for recruiter registration')
      return
    }

    // Prefer backend registration so we can use service role and send email.
    const BACKEND_URL = window.SKREENIT_BACKEND_URL || 'https://skreenit-backend.onrender.com'
    const fd = new FormData()
    fd.append('full_name', full_name)
    fd.append('email', email)
    fd.append('mobile', mobile)
    fd.append('location', location)
    fd.append('role', role)
    if (company_id) fd.append('company_id', company_id)
    if (resumeFile) fd.append('resume', resumeFile)

    let backendOk = false
    try {
      const resp = await fetch(`${BACKEND_URL}/auth/register`, {
        method: 'POST',
        body: fd,
        // CORS handled by backend; no credentials needed
      })
      if (!resp.ok) {
        const text = await resp.text()
        throw new Error(`Backend error ${resp.status}: ${text}`)
      }
      const data = await resp.json().catch(() => ({}))
      backendOk = true
      // Inform the user
      alert('Registration successful! Please check your email for your temporary password and next steps.')
      window.location.href = 'https://login.skreenit.com/'
      return
    } catch (be) {
      console.warn('Backend register failed, falling back to client-side:', be)
    }

    if (!backendOk) {
      // Fallback: client-side sign up (no email, RLS might block DB insert)
      const tempPassword = generateTempPassword(12)
      const { data: signUpRes, error: signUpError } = await supabase.auth.signUp({
        email,
        password: tempPassword,
        options: { data: { full_name, mobile, location, role, first_login: true } }
      })
      if (signUpError) throw signUpError
      const authUser = signUpRes.user
      if (!authUser) throw new Error('Sign up failed')

      // Optional file upload (may fail if bucket policies are strict)
      if (role === 'candidate' && resumeFile) {
        const path = `${authUser.id}/${Date.now()}-${resumeFile.name}`
        const { error: upErr } = await storage.uploadFile('resumes', path, resumeFile)
        if (upErr) console.warn('Resume upload failed:', upErr)
      }

      alert('Registration successful (fallback). Please check your email if you received one, or use the temporary password shown earlier.')
      window.location.href = 'https://login.skreenit.com/'
    }
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

    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw error

    const user = data.user
    const firstLogin = user?.user_metadata?.first_login === true
    const role = user?.user_metadata?.role

    localStorage.setItem('skreenit_role', role)
    localStorage.setItem('skreenit_user_id', user.id)

    if (firstLogin) {
      window.location.href = '/login/update-password.html'
      return
    }

    if (role === 'candidate') {
      window.location.href = 'https://applicants.skreenit.com/'
    } else if (role === 'recruiter') {
      window.location.href = 'https://recruiter.skreenit.com/'
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
  initEmail()

  const form = e.currentTarget
  const submitBtn = form.querySelector('button[type="submit"]')
  setLoading(submitBtn, true)

  try {
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

    await supabase.auth.updateUser({ data: { first_login: false } })

    alert('Password updated successfully! Redirecting...')

    const role = user.user_metadata?.role
    if (role === 'candidate') {
      window.location.href = 'https://applicants.skreenit.com/'
    } else if (role === 'recruiter') {
      window.location.href = 'https://recruiter.skreenit.com/'
    } else {
      window.location.href = 'https://login.skreenit.com/'
    }
  } catch (err) {
    console.error('Update password error:', err)
    showError(err.message || 'Update failed')
  } finally {
    setLoading(submitBtn, false)
  }
}
