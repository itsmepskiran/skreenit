// auth/assets/js/auth-pages.js

import { supabase } from './supabase-config.js'
import { backendUploadFile, handleResponse, backendUrl } from './backend-client.js'

// -------- Auth State Handling --------

// Listen for authentication events (e.g., after email confirmation)
// This ensures the session is captured when the user lands on the update-password page.
supabase.auth.onAuthStateChange(async (event, session) => {
  if (event === 'SIGNED_IN') {
    // User has signed in (e.g., via the confirmation link).
    // Persist the session to make it available for the password update.
    await persistSessionToLocalStorage();
    console.log('User signed in, session persisted.');

  } else if (event === 'PASSWORD_RECOVERY') {
    // This event is fired when the user is redirected from a password recovery link
    // The session is now active, and the user can update their password.
    console.log('Password recovery session started.');
  }
});

// -------- Utilities --------

// Send email to recruiter with user ID and Company ID after email confirmation
async function sendRecruiterEmail(user, companyId) {
  if (user?.user_metadata?.role !== 'recruiter') return;

  try {
    await fetch(`${backendUrl()}/api/send-recruiter-email`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('skreenit_token')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        userId: user.id,
        companyId: companyId,
        email: user.email,
      }),
    });
    console.log('Recruiter credentials email sent successfully.');
  } catch (error) {
    console.error('Error sending recruiter email:', error);
  }
}


// Generate a strong temporary password for the initial Supabase signUp
function generateTempPassword(length = 16) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_=+[]{};:,.?'
  let out = ''
  for (let i = 0; i < length; i++) out += chars[Math.floor(Math.random() * chars.length)]
  return out
}

// Persist session and user info for use across subdomains/pages
async function persistSessionToLocalStorage() {
  try {
    const { data: sessionData } = await supabase.auth.getSession()
    const { data: userData } = await supabase.auth.getUser()
    const access_token = sessionData?.session?.access_token || ''
    const refresh_token = sessionData?.session?.refresh_token || ''
    const user = userData?.user || null

    if (access_token) localStorage.setItem('skreenit_token', access_token)
    if (refresh_token) localStorage.setItem('skreenit_refresh_token', refresh_token)
    if (user?.id) localStorage.setItem('skreenit_user_id', user.id)
    const role = user?.user_metadata?.role
    if (role) localStorage.setItem('skreenit_role', role)
  } catch (e) {
    console.warn('Failed to persist session to localStorage', e)
  }
}

// Role-based redirect after login with first-time login handling
async function redirectByRole(defaultUrl = 'https://dashboard.skreenit.com/candidate-dashboard.html') {
  const role = localStorage.getItem('skreenit_role')
  const userId = localStorage.getItem('skreenit_user_id')
  
  try {
    // Check if this is first-time login by checking user profile completion
    const { data: { user } } = await supabase.auth.getUser()
    const isFirstTimeLogin = user?.user_metadata?.first_time_login === true
    const hasUpdatedPassword = user?.user_metadata?.password_updated === true
    
  if (role === 'recruiter') {
      if (isFirstTimeLogin) {
        // First-time recruiter goes to profile setup
        window.location.href = 'https://recruiter.skreenit.com/recruiter-profile.html'
      } else {
        // Returning recruiter goes to dashboard
        window.location.href = 'https://dashboard.skreenit.com/recruiter-dashboard.html'
      }
  } else if (role === 'candidate') {
      if (isFirstTimeLogin) {
        // First-time candidate goes to detailed application form
        window.location.href = 'https://applicant.skreenit.com/detailed-application-form.html'
      } else {
        // Returning candidate goes to dashboard
        window.location.href = 'https://dashboard.skreenit.com/candidate-dashboard.html'
      }
  } else {
    window.location.href = defaultUrl
  }
  } catch (error) {
    console.error('Error checking first-time login:', error)
    // Fallback to default behavior
    if (role === 'recruiter') {
      window.location.href = 'https://dashboard.skreenit.com/recruiter-dashboard.html'
    } else {
      window.location.href = 'https://dashboard.skreenit.com/candidate-dashboard.html'
    }
  }
}

// -------- Handlers --------

// Registration: user provides basic details; Supabase sends verification email.
// After email verification, user is redirected to update-password page.
export async function handleRegistrationSubmit(event) {
  event.preventDefault()
  const form = event.target
  const submitBtn = form.querySelector('button[type="submit"]')
  const originalText = submitBtn?.textContent || 'Register'
  if (submitBtn) { submitBtn.textContent = 'Registering...'; submitBtn.disabled = true }

  try {
    const fd = new FormData(form)
    const full_name = (fd.get('full_name') || '').trim()
    const email = (fd.get('email') || '').trim()
    const mobile = (fd.get('mobile') || '').trim()
    const location = (fd.get('location') || '').trim()
    const role = (fd.get('role') || '').trim()
    const company_name = (fd.get('company_name') || '').trim()
    const resume = fd.get('resume')

    // Validate role selection and required fields
    if (!role || !['candidate', 'recruiter'].includes(role)) {
      throw new Error('Please select a valid role (Candidate or Recruiter)')
    }
    if (!full_name || !email || !mobile || !location) {
      throw new Error('Please fill in all required fields')
    }

    // Basic validations
    const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
    if (!emailOk) throw new Error('Please enter a valid email address')
    if (mobile.length < 7) throw new Error('Please enter a valid mobile number')

    // Recruiter must provide company name
    if (role === 'recruiter' && !company_name) throw new Error('Company name is required for recruiters')

    // Prepare payload for backend
    const bfd = new FormData()
    bfd.append('full_name', full_name)
    bfd.append('email', email)
    bfd.append('mobile', mobile)
    bfd.append('location', location)
    bfd.append('role', role)
    if (company_name) bfd.append('company_name', company_name)
    if (resume && resume.size > 0) bfd.append('resume', resume)

    const resp = await backendUploadFile('/auth/register', bfd)
    const result = await handleResponse(resp)
    if (!result || result.ok === false) throw new Error(result?.error || 'Registration failed')

    // Replace form body with thank-you content
    const formEl = document.querySelector('.auth-body')
    if (formEl) {
      formEl.innerHTML = `
        <div id="thankYou" class="thank-you-message">
          <i class="fas fa-check-circle success-icon"></i>
          <h2>Thank You for registering with us!</h2>
          <p>Please check your email for the verification link and further instructions.</p>
          <a href="https://login.skreenit.com/login.html" class="btn btn-primary">Go to Login</a>
        </div>
      `
    }

    return true
  } catch (err) {
    console.error('Registration error:', err)
    notify(err.message || 'Registration failed. Please try again.', 'error')
    return false
  } finally {
    if (submitBtn) { submitBtn.textContent = originalText; submitBtn.disabled = false }
  }
}

// Update Password after the email verification link opens update-password page.
// Requires the email link to have created a valid session.
export async function handleUpdatePasswordSubmit(event) {
  event.preventDefault()
  const form = event.target
  const submitBtn = form.querySelector('button[type="submit"]')
  const originalText = submitBtn?.textContent || 'Update Password'
  if (submitBtn) { submitBtn.textContent = 'Updating...'; submitBtn.disabled = true }

  try {
    const fd = new FormData(form)
    const new_password = (fd.get('new_password') || '').trim()
    const confirm_password = (fd.get('confirm_password') || '').trim()
    if (new_password.length < 8) throw new Error('Password must be at least 8 characters.')
    if (new_password !== confirm_password) throw new Error('Passwords do not match.')

    const hash = window.location.hash
    const token = new URLSearchParams(hash.slice(1)).get('access_token')
    if (!token) throw new Error('Missing access token. Please use the link from your email.')

    const { error } = await supabase.auth.updateUser(
      { password: new_password },
      { accessToken: token }
    )
    if (error) throw new Error(error.message)
    // Notify backend about password update (for email notifications)
    try {
      // After a successful password update, the session is refreshed.
      // We must get the new session data to ensure we have a valid token.
      const { data: { session }, error: sessionError } = await supabase.auth.getSession();
      if (sessionError) throw new Error('Could not retrieve session after password update.');
      
      const token = session?.access_token;
      if (!token) throw new Error('No valid token found after password update.');

      const response = await fetch(`${backendUrl()}/auth/password-updated`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      const result = await response.json();
      if (!result || result.ok === false) {
        throw new Error(result?.error || 'Failed to update password on backend.');
      }

    } catch (e) {
      console.warn('Failed to notify backend about password update:', e);
      // Non-critical error, so we don't block the user.
    }

    notify('Password updated successfully! Redirecting to login...', 'success')
    setTimeout(() => {
      window.location.href = 'https://login.skreenit.com/login.html'
    }, 5000)
  } catch (err) {
    console.error('Update password error:', err)
    notify(err.message || 'Failed to update password. Please try again.', 'error')
  } finally {
    if (submitBtn) { submitBtn.textContent = originalText; submitBtn.disabled = false }
  }
}

// Login with email + password, store session/role, and redirect by role
export async function handleLoginSubmit(event) {
  event.preventDefault()
  const form = event.target
  const submitBtn = form.querySelector('button[type="submit"]')
  const originalText = submitBtn?.textContent || 'Login'
  if (submitBtn) { submitBtn.textContent = 'Signing in...'; submitBtn.disabled = true }

  try {
    const fd = new FormData(form)
    const role = (fd.get('role') || '').trim() // used for UI, we still trust role from user_metadata
    const email = (fd.get('email') || '').trim()
    const password = (fd.get('password') || '').trim()
    const company_id = (fd.get('company_id') || '').trim() // optional recruiter context

    if (!email || !password) throw new Error('Email and password are required.')

    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw new Error(error.message)

    // Persist session + role in localStorage for downstream pages
    await persistSessionToLocalStorage()

    // Optional: you can pass company_id to backend if needed (e.g., validate company mapping)
    // try { await backendFetch('/auth/login-meta', { method: 'POST', body: JSON.stringify({ company_id }), headers: { 'Content-Type': 'application/json' } }) } catch {}

    // Redirect by role from user_metadata
    redirectByRole()
  } catch (err) {
    console.error('Login error:', err)
    notify(err.message || 'Login failed. Please try again.', 'error')
  } finally {
    if (submitBtn) { submitBtn.textContent = originalText; submitBtn.disabled = false }
  }
}