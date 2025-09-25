// Auth Pages Logic - Skreenit Edition
import { supabase, auth, db, storage } from './supabase-config.js'

// Resend integration note:
// Resend should be used server-side only. Do not expose API keys in the browser.
// These stubs are kept to avoid runtime errors where initEmail() was called.
function emailEnabled() {
  // Always false on client; email is sent by backend using Resend.
  return false
}

function initEmail() {
  // No-op. If needed, ensure backend endpoints handle email via Resend.
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
  e.preventDefault();
  // initEmail removed: Resend is handled server-side.

  const form = e.currentTarget;
  const submitBtn = form.querySelector('button[type="submit"]');
  setLoading(submitBtn, true);

  try {
    const full_name = getFormValue(form, 'full_name');
    const email = getFormValue(form, 'email');
    const mobile = getFormValue(form, 'mobile');
    const location = getFormValue(form, 'location');
    const role = getFormValue(form, 'role');
    const company_id = getFormValue(form, 'company_id');
    const resumeFile = getFile(form, 'resume');

    if (!full_name || !email || !mobile || !location || !role) {
      showError('Please fill all required fields');
      return false;
    }

    if (role === 'recruiter' && !company_id) {
      showError('Company ID is required for recruiter registration');
      return false;
    }

    const BACKEND_URL = window.SKREENIT_BACKEND_URL || 'https://skreenit-api.onrender.com';
    const fd = new FormData();
    fd.append('full_name', full_name);
    fd.append('email', email);
    fd.append('mobile', mobile);
    fd.append('location', location);
    fd.append('role', role);
    if (company_id) fd.append('company_id', company_id);
    if (resumeFile) fd.append('resume', resumeFile);

    let backendOk = false;

    try {
      const resp = await fetch(`${BACKEND_URL}/auth/register`, {
        method: 'POST',
        body: fd,
      });

      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(`Backend error ${resp.status}: ${text}`);
      }

      backendOk = true;
      // Let page handle thank-you display and redirect
      return true;
    } catch (be) {
      console.warn('Backend register failed, falling back to client-side:', be);
    }

    if (!backendOk) {
      const tempPassword = generateTempPassword(12);
      const { data: signUpRes, error: signUpError } = await supabase.auth.signUp({
        email,
        password: tempPassword,
        options: {
          data: { full_name, mobile, location, role, first_login: true }
        }
      });

      if (signUpError) throw signUpError;

      const authUser = signUpRes.user;
      if (!authUser) throw new Error('Sign up failed');

      if (role === 'candidate' && resumeFile) {
        const path = `${authUser.id}/${Date.now()}-${resumeFile.name}`;
        const { error: upErr } = await storage.uploadFile('resumes', path, resumeFile);
        if (upErr) console.warn('Resume upload failed:', upErr);
      }

      // Let page handle thank-you display and redirect
      return true;
    }
  } catch (err) {
    console.error('Registration error:', err);
    showError(err.message || 'Registration failed');
    return false;
  } finally {
    setLoading(form.querySelector('button[type="submit"]'), false);
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

    // Persist access token for backend Authorization headers on this subdomain
    try {
      const { data: sessionData } = await supabase.auth.getSession()
      const token = sessionData?.session?.access_token
      if (token) localStorage.setItem('skreenit_token', token)
    } catch {}

    if (firstLogin) {
      window.location.href = 'https://auth.skreenit.com/update-password.html'
      return
    }

    if (role === 'candidate') {
      window.location.href = 'https://applicant.skreenit.com/detailed-application-form.html'
    } else if (role === 'recruiter') {
      window.location.href = 'https://recruiter.skreenit.com/recruiter-profile.html'
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

    // Notify backend to send password-changed email via Resend (best-effort)
    try {
      const BACKEND_URL = window.SKREENIT_BACKEND_URL || 'https://skreenit-api.onrender.com'
      await fetch(`${BACKEND_URL}/auth/password-changed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: user.email,
          full_name: user.user_metadata?.full_name || null,
        }),
      })
    } catch (notifyErr) {
      console.warn('Password-changed notification failed:', notifyErr)
    }

    alert('Password Changed. Please login with New Password')
    window.location.href = 'https://login.skreenit.com/'
  } catch (err) {
    console.error('Update password error:', err)
    showError(err.message || 'Update failed')
  } finally {
    setLoading(submitBtn, false)
  }
}
