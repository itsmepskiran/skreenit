// Auth Pages Logic - Skreenit (auth subdomain)
import { supabase, auth, db, storage } from './supabase-config.js'

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
  try { if (emailEnabled()) window.emailjs.init(EMAILJS_PUBLIC_KEY) } catch {}
}

function showError(message) {
  const el = document.getElementById('formError')
  if (el) el.textContent = message
  else alert(message)
}

function generateTempPassword(length = 12) {
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
  if (!btn.dataset.originalText) btn.dataset.originalText = btn.textContent
  btn.disabled = loading
  btn.textContent = loading ? 'Please wait...' : btn.dataset.originalText
}

export function wireRegistrationPage() {
  const roleSelect = document.getElementById('role')
  const candidateFields = document.getElementById('candidateFields')
  const recruiterFields = document.getElementById('recruiterFields')
  const companyIdInput = document.getElementById('company_id')
  if (!roleSelect) return
  const apply = () => {
    const role = roleSelect.value
    candidateFields?.classList.toggle('hidden', role !== 'candidate')
    recruiterFields?.classList.toggle('hidden', role !== 'recruiter')
    if (companyIdInput) companyIdInput.required = role === 'recruiter'
  }
  roleSelect.addEventListener('change', apply)
  apply()
}

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
      return false
    }
    if (role === 'recruiter' && !company_id) {
      showError('Company ID is required for recruiter registration')
      return false
    }

    const tempPassword = generateTempPassword(12)

    const { data: signUpRes, error: signUpError } = await supabase.auth.signUp({
      email,
      password: tempPassword,
      options: { data: { full_name, mobile, location, role, first_login: true } }
    })
    if (signUpError) throw signUpError
    const authUser = signUpRes.user
    if (!authUser) throw new Error('Sign up failed')

    let resume_url = null
    if (role === 'candidate' && resumeFile) {
      const path = `${authUser.id}/${Date.now()}-${resumeFile.name}`
      const { error: upErr } = await storage.uploadFile('resumes', path, resumeFile)
      if (upErr) throw upErr
      resume_url = storage.getPublicUrl('resumes', path)
    }

    await db.insert('users', [{
      id: authUser.id,
      full_name,
      email,
      mobile,
      location,
      role,
      company_id: role === 'recruiter' ? company_id : null,
      resume_url: role === 'candidate' ? resume_url : null
    }])

    // Optionally send email using EmailJS if configured
    try {
      if (emailEnabled()) {
        await window.emailjs.send(EMAILJS_SERVICE_ID, EMAILJS_TEMPLATE_ID_REG, {
          to_email: email,
          user_id: email,
          temp_password: tempPassword,
          full_name
        })
      }
    } catch {}

    return true
  } catch (err) {
    console.error('Registration error:', err)
    showError(err.message || 'Registration failed')
    return false
  } finally {
    setLoading(submitBtn, false)
  }
}

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
      window.location.href = './update-password.html'
      return
    }

    if (role === 'candidate') window.location.href = 'https://applicants.skreenit.com/detailed-application-form.html'
    else if (role === 'recruiter') window.location.href = 'https://recruiter.skreenit.com/'
    else showError('Logged in, but role not set. Please contact support.')
  } catch (err) {
    console.error('Login error:', err)
    showError(err.message || 'Login failed')
  } finally {
    setLoading(submitBtn, false)
  }
}

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
    // Redirect to login.skreenit.com (as requested)
    window.location.href = 'https://login.skreenit.com/'
  } catch (err) {
    console.error('Update password error:', err)
    showError(err.message || 'Update failed')
  } finally {
    setLoading(submitBtn, false)
  }
}
