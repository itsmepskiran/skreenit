import { supabase, jobService, applicationService, realtimeService } from './supabase-config.js'

const dashboardContent = document.getElementById('dashboardContent')
const candidateName = document.getElementById('candidateName')
const dashboardError = document.getElementById('dashboardError')

let currentUser = null

async function checkAuth() {
  const { data, error } = await supabase.auth.getUser()
  if (error || !data?.user) {
    window.location.href = 'login.html'
    return
  }
  currentUser = data.user
  const role = currentUser.user_metadata?.role
  if (role !== 'candidate') {
    window.location.href = 'login.html'
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

async function renderJobs() {
  clearContent()
  try {
    const jobs = await jobService.getRecommendedJobs(currentUser.id)
    if (!jobs.length) {
      dashboardContent.innerHTML = `<p>No job matches found. Please check back later.</p>`
      return
    }
    const jobList = jobs.map(job => `
      <div class="job-card">
        <h3>${job.title}</h3>
        <p>${job.description}</p>
        <button onclick="applyToJob('${job.id}')">Apply</button>
      </div>
    `).join('')
    dashboardContent.innerHTML = `<section><h2>Job Matches</h2>${jobList}</section>`
  } catch (err) {
    console.error(err)
    showError('Failed to load job matches.')
  }
}

async function renderApplications() {
  clearContent()
  try {
    const apps = await applicationService.getApplicationsByUser(currentUser.id)
    if (!apps.length) {
      dashboardContent.innerHTML = `<p>You haven’t applied to any jobs yet.</p>`
      return
    }
    const appList = apps.map(app => `
      <div class="application-card">
        <h3>${app.job_title}</h3>
        <p>Status: ${app.status}</p>
        <p>Applied on: ${new Date(app.created_at).toLocaleDateString()}</p>
      </div>
    `).join('')
    dashboardContent.innerHTML = `<section><h2>Your Applications</h2>${appList}</section>`
  } catch (err) {
    console.error(err)
    showError('Failed to load applications.')
  }
}

function renderInterview() {
  clearContent()
  dashboardContent.innerHTML = `
    <section>
      <h2>Video Interview</h2>
      <p>Coming soon: record answers to common questions and submit your video profile.</p>
    </section>
  `
}

function applyToJob(jobId) {
  alert(`Apply logic for job ${jobId} will be wired here.`)
}

function logout() {
  supabase.auth.signOut().then(() => {
    localStorage.clear()
    window.location.href = 'login.html'
  })
}

function route() {
  const hash = window.location.hash || '#profile'
  switch (hash) {
    case '#profile': renderProfile(); break
    case '#jobs': renderJobs(); break
    case '#applications': renderApplications(); break
    case '#interview': renderInterview(); break
    default: renderProfile(); break
  }
}

window.addEventListener('hashchange', route)

checkAuth().then(route)
