import { supabase } from './supabase-config.js'

async function requireAuth(roleRequired) {
  const { data, error } = await supabase.auth.getUser()
  if (error || !data?.user) {
    window.location.href = 'https://auth.skreenit.com/login.html'
    return null
  }
  const user = data.user
  const role = user.user_metadata?.role
  if (role !== roleRequired) {
    // wrong role, send to appropriate site
    if (role === 'recruiter') window.location.href = 'https://dashboards.skreenit.com/recruiter-dashboard.html'
    else window.location.href = 'https://auth.skreenit.com/login.html'
    return null
  }
  return user
}

(async function init() {
  const user = await requireAuth('candidate')
  if (!user) return
  // Minimal: inject user name
  const els = document.getElementsByClassName('user-name')
  Array.from(els).forEach(el => el.textContent = user.user_metadata?.full_name || 'Candidate')

  // Nav handling (stub)
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
      document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'))
      item.classList.add('active')
    })
  })

  document.getElementById('logoutBtn')?.addEventListener('click', async () => {
    await supabase.auth.signOut()
    window.location.href = 'https://auth.skreenit.com/login.html'
  })
})()
