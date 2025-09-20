import { supabase } from './supabase-config.js'

const dashboardContent = document.getElementById('dashboardContent')
const candidateName = document.getElementById('candidateName')
const dashboardError = document.getElementById('dashboardError')

let currentUser = null

async function checkAuth() {
  const { data, error } = await supabase.auth.getUser()
  if (error || !data?.user) {
    window.location.href = 'https://login.skreenit.com/'
    return
  }
  currentUser = data.user
  const role = currentUser.user_metadata?.role
  if (role !== 'candidate') {
    window.location.href = 'https://login.skreenit.com/'
    return
  }
  candidateName.textContent = currentUser.user_metadata?.full_name || 'Candidate'
  localStorage.setItem('skreenit_user_id', currentUser.id)
  localStorage.setItem('skreenit_role', role)
}

function showError(message) {
  dashboardError.textContent = message
}

function clearContent() {
  dashboardContent.innerHTML = ''
}

function renderProfile() {
  clearContent()
  const profile = currentUser.user_metadata
  dashboardContent.innerHTML = `
    <section>
      <h2>Your Profile</h2>
      <p><strong>Name:</strong> ${profile.full_name}</p>
      <p><strong>Email:</strong> ${currentUser.email}</p>
      <p><strong>Mobile:</strong> ${profile.mobile}</p>
      <p><strong>Location:</strong> ${profile.location}</p>
      <p><strong>Resume:</strong> ${profile.resume_url ? `<a href="${profile.resume_url}" target="_blank">View</a>` : 'Not uploaded'}</p>
    </section>
  `
}

function route() {
  const hash = window.location.hash || '#profile'
  switch (hash) {
    case '#profile': renderProfile(); break
    default: renderProfile(); break
  }
}

window.addEventListener('hashchange', route)

checkAuth().then(route)
