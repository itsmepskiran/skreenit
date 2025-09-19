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
    if (role === 'candidate') window.location.href = 'https://dashboards.skreenit.com/candidate-dashboard.html'
    else window.location.href = 'https://auth.skreenit.com/login.html'
    return null
  }
  return user
}

(async function init() {
  const user = await requireAuth('recruiter')
  if (!user) return

  const els = document.getElementsByClassName('user-name')
  Array.from(els).forEach(el => el.textContent = user.user_metadata?.full_name || 'Recruiter')

  document.getElementById('logoutBtn')?.addEventListener('click', async () => {
    await supabase.auth.signOut()
    window.location.href = 'https://auth.skreenit.com/login.html'
  })
})()
