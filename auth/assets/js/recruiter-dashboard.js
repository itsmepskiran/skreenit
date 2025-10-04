import { supabase } from './supabase-config.js'
import { backendFetch } from './backend-client.js'

let currentUser = null

// Bootstrap session from URL fragment (access_token/refresh_token) if present, and persist basic info
(async function bootstrapSessionFromHash() {
  try {
    const hash = window.location.hash ? window.location.hash.substring(1) : ''
    if (!hash) return
    const params = new URLSearchParams(hash)
    const at = params.get('access_token')
    const rt = params.get('refresh_token')
    const uid = params.get('user_id')
    const role = params.get('role')
    if (uid) localStorage.setItem('skreenit_user_id', uid)
    if (role) localStorage.setItem('skreenit_role', role)
    if (at) localStorage.setItem('skreenit_token', at)
    if (at && rt) {
      try { await supabase.auth.setSession({ access_token: at, refresh_token: rt }) } catch {}
    }
    // Clean hash to avoid reprocessing on reload
    history.replaceState(null, document.title, window.location.pathname + window.location.search)
  } catch {}
})()

function qs(sel) { return document.querySelector(sel) }
function el(html) { const d = document.createElement('div'); d.innerHTML = html.trim(); return d.firstChild }

async function checkAuth() {
  const { data, error } = await supabase.auth.getUser()
  if (error || !data?.user) {
    window.location.href = 'https://login.skreenit.com/login.html'
    throw new Error('Not authenticated')
  }
  const user = data.user
  if (user?.user_metadata?.role !== 'recruiter') {
    window.location.href = 'https://login.skreenit.com/login.html'
    throw new Error('Wrong role')
  }
  currentUser = user
  localStorage.setItem('skreenit_user_id', user.id)
  localStorage.setItem('skreenit_role', 'recruiter')
  const nameEl = document.querySelector('.user-name')
  if (nameEl) nameEl.textContent = user.user_metadata?.full_name || 'Recruiter'

  // Persist access token for Authorization headers on this subdomain
  try {
    const { data: sessionData } = await supabase.auth.getSession()
    const token = sessionData?.session?.access_token
    if (token) localStorage.setItem('skreenit_token', token)
  } catch {}
}

function mountContent(node) {
  const main = qs('.main-content')
  if (!main) return
  main.innerHTML = ''
  main.appendChild(node)
}

function setActiveNav(hash) {
  const items = document.querySelectorAll('.nav-menu .nav-item')
  items.forEach(li => {
    const section = li.getAttribute('data-section')
    if ('#' + section === hash) li.classList.add('active')
    else li.classList.remove('active')
  })
}

function renderOverview() {
  const node = el(`
    <section id="overviewSection" class="dashboard-section">
      <div class="section-header" style="display:flex;align-items:center;justify-content:space-between;gap:.75rem;flex-wrap:wrap;">
        <h1 style="margin:0;">Dashboard Overview</h1>
        <div style="display:flex;gap:.5rem;flex-wrap:wrap;">
          <a class="btn btn-secondary" href="https://recruiter.skreenit.com/recruiter-profile.html">Edit/Update Profile</a>
          <button class="btn btn-primary"><i class="fas fa-plus"></i> Create Job</button>
        </div>
      </div>
      <div class="card" style="background:#fff;border-radius:12px;padding:1rem;box-shadow:0 2px 10px rgba(0,0,0,.06);margin-bottom:1rem;">
        <h3 style="margin-top:0;display:flex;align-items:center;gap:.5rem;"><i class="fas fa-check"></i> Approve Application</h3>
        <form id="approveForm" style="display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;">
          <input type="text" id="applicationIdInput" placeholder="Application ID" required style="flex:1;min-width:260px;" />
          <button type="submit" class="btn btn-primary">Approve</button>
        </form>
      </div>
      <div class="card" style="background:#fff;border-radius:12px;padding:1rem;box-shadow:0 2px 10px rgba(0,0,0,.06);margin-bottom:1rem;">
        <h3 style="margin-top:0;display:flex;align-items:center;gap:.5rem;"><i class="fas fa-file-alt"></i> View Resume</h3>
        <form id="viewResumeForm" style="display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;">
          <input type="text" id="resumeApplicationIdInput" placeholder="Application ID" required style="flex:1;min-width:260px;" />
          <button type="submit" class="btn btn-secondary">Get Resume</button>
        </form>
      </div>
      <div class="card" style="background:#fff;border-radius:12px;padding:1rem;box-shadow:0 2px 10px rgba(0,0,0,.06);margin-bottom:1rem;">
        <h3 style="margin-top:0;display:flex;align-items:center;gap:.5rem;"><i class="fas fa-question-circle"></i> Job Questions</h3>
        <form id="questionsForm" style="display:grid;gap:.5rem;">
          <input type="text" id="jobIdInput" placeholder="Job ID" required />
          <textarea id="questionsText" rows="6" placeholder="Enter one question per line"></textarea>
          <div style="display:flex;gap:.5rem;flex-wrap:wrap;">
            <button type="submit" class="btn btn-primary">Save Questions</button>
            <button type="button" id="listQuestionsBtn" class="btn btn-secondary">List Questions</button>
          </div>
        </form>
        <div id="questionsList" style="margin-top:.5rem;"></div>
      </div>

      <div class="card" style="background:#fff;border-radius:12px;padding:1rem;box-shadow:0 2px 10px rgba(0,0,0,.06);margin-bottom:1rem;">
        <h3 style="margin-top:0;display:flex;align-items:center;gap:.5rem;"><i class="fas fa-video"></i> Candidate General Video & Scores</h3>
        <form id="viewGeneralVideoForm" style="display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;margin-bottom:1rem;">
          <input type="text" id="candidateIdInput" placeholder="Candidate ID" required style="flex:1;min-width:260px;" />
          <button type="submit" class="btn btn-secondary">Load General Video</button>
        </form>
        <div id="generalVideoResult" style="display:none">
          <div id="generalVideoScores" style="margin:.5rem 0"></div>
          <video id="generalVideoPlayer" controls style="max-width:100%;height:auto"></video>
        </div>
        <div id="generalVideoEmpty" style="color:#718096">Enter a Candidate ID to load general video and analysis.</div>
      </div>
    </section>
  `)

  node.querySelector('#approveForm').addEventListener('submit', async (e) => {
    e.preventDefault()
    const appId = node.querySelector('#applicationIdInput').value.trim()
    if (!appId) return
    try {
      const token = localStorage.getItem('skreenit_token')
      const resp = await backendFetch(`/recruiter/application/${appId}/approve`, {
        method: 'POST',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        }
      })
      if (!resp.ok) throw new Error('Approve failed')
      alert('Application moved to Under Review. Candidate notified (best-effort).')
    } catch (err) {
      alert('Failed to approve application')
    }
  })

  node.querySelector('#viewResumeForm').addEventListener('submit', async (e) => {
    e.preventDefault()
    const appId = node.querySelector('#resumeApplicationIdInput').value.trim()
    if (!appId) return
    try {
      const token = localStorage.getItem('skreenit_token')
      const resp = await backendFetch(`/recruiter/application/${appId}/resume-url`, {
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        }
      })
      const data = await resp.json()
      if (!resp.ok) throw new Error(data?.detail || 'Failed to get resume URL')
      const url = data?.resume_url
      if (url) {
        window.open(url, '_blank', 'noopener')
      } else {
        alert('Resume URL not available')
      }
    } catch (err) {
      alert('Failed to fetch resume URL')
    }
  })

  node.querySelector('#questionsForm').addEventListener('submit', async (e) => {
    e.preventDefault()
    const jobId = node.querySelector('#jobIdInput').value.trim()
    const lines = node.querySelector('#questionsText').value.split('\n').map(s => s.trim()).filter(Boolean)
    const payload = lines.map((q, i) => ({ question_text: q, question_order: i + 1, time_limit: 120 }))
    try {
      const token = localStorage.getItem('skreenit_token')
      const resp = await backendFetch(`/recruiter/job/${jobId}/questions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(payload)
      })
      if (!resp.ok) throw new Error('Save failed')
      alert('Questions saved')
    } catch (err) {
      alert('Failed to save questions')
    }
  })

  node.querySelector('#listQuestionsBtn').addEventListener('click', async () => {
    const jobId = node.querySelector('#jobIdInput').value.trim()
    if (!jobId) return
    const listEl = node.querySelector('#questionsList')
    listEl.textContent = 'Loading...'
    try {
      const token = localStorage.getItem('skreenit_token')
      const resp = await backendFetch(`/recruiter/job/${jobId}/questions`, {
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        }
      })
      const data = await resp.json()
      if (!resp.ok) throw new Error(data?.detail || 'Fetch failed')
      listEl.innerHTML = '<ol>' + (data.questions || []).map(q => `<li>${q.question_text}</li>`).join('') + '</ol>'
    } catch (err) {
      listEl.textContent = 'Failed to load questions'
    }
  })

  // Load candidate general video + scores
  node.querySelector('#viewGeneralVideoForm').addEventListener('submit', async (e) => {
    e.preventDefault()
    const candidateId = node.querySelector('#candidateIdInput').value.trim()
    if (!candidateId) return
    const out = node.querySelector('#generalVideoResult')
    const empty = node.querySelector('#generalVideoEmpty')
    const vid = node.querySelector('#generalVideoPlayer')
    const scoresDiv = node.querySelector('#generalVideoScores')
    try {
      const token = localStorage.getItem('skreenit_token')
      const resp = await backendFetch(`/applicant/general-video/${candidateId}`, {
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
      })
      const data = await resp.json()
      if (!resp.ok) throw new Error(data?.detail || 'Failed')
      empty.style.display = 'none'
      out.style.display = 'block'
      vid.src = data.video_url || ''
      scoresDiv.innerHTML = data.scores ? (
        `<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:.5rem;">
          ${Object.entries(data.scores).map(([k,v]) => `<div class=\"stat-card\"><div class=\"stat-info\"><span class=\"stat-number\">${v}</span><span class=\"stat-label\">${k}</span></div></div>`).join('')}
        </div>`
      ) : '<em>No scores available</em>'
    } catch (e) {
      out.style.display = 'none'
      empty.style.display = 'block'
      empty.textContent = 'Failed to load general video'
    }
  })

  mountContent(node)
}

function renderJobs() {
  const node = el(`
    <section class="dashboard-section">
      <div class="section-header"><h1>Jobs</h1><button class="btn btn-primary"><i class="fas fa-plus"></i> Create Job</button></div>
      <div id="jobsHost" class="card" style="background:#fff;border-radius:12px;padding:1rem;box-shadow:0 2px 10px rgba(0,0,0,.06);">
        <em>Jobs listing will appear here.</em>
      </div>
    </section>
  `)
  mountContent(node)
}

function renderCandidates() {
  const node = el(`
    <section class="dashboard-section">
      <div class="section-header"><h1>Candidates</h1></div>
      <div id="candsHost" class="card" style="background:#fff;border-radius:12px;padding:1rem;box-shadow:0 2px 10px rgba(0,0,0,.06);">
        <em>Applicants and their statuses will appear here.</em>
      </div>
    </section>
  `)
  mountContent(node)
}

function renderAnalytics() {
  const node = el(`
    <section class="dashboard-section">
      <div class="section-header"><h1>Analytics</h1></div>
      <div class="stats-grid">
        <div class="stat-card"><div class="stat-info"><span class="stat-number">--</span><span class="stat-label">Views</span></div></div>
        <div class="stat-card"><div class="stat-info"><span class="stat-number">--</span><span class="stat-label">Applications</span></div></div>
        <div class="stat-card"><div class="stat-info"><span class="stat-number">--</span><span class="stat-label">Shortlisted</span></div></div>
      </div>
    </section>
  `)
  mountContent(node)
}

async function render() {
  const hash = window.location.hash || '#overview'
  setActiveNav(hash)
  if (hash === '#jobs') return renderJobs()
  if (hash === '#candidates') return renderCandidates()
  if (hash === '#analytics') return renderAnalytics()
  return renderOverview()
}

// Sidebar clicks -> change hash
;(function bindNav(){
  document.querySelectorAll('.nav-menu .nav-item').forEach(li => {
    li.addEventListener('click', () => {
      const section = li.getAttribute('data-section')
      if (section) window.location.hash = '#' + section
    })
  })
})()

// Logout handler (robust)
;(function bindLogout(){
  function doRedirect(){ window.location.href = 'https://login.skreenit.com/login.html' }
  async function doLogout(){
    try {
      try {
        localStorage.removeItem('skreenit_token')
        localStorage.removeItem('skreenit_refresh_token')
        localStorage.removeItem('skreenit_user_id')
        localStorage.removeItem('skreenit_role')
      } catch {}
      await Promise.race([
        supabase.auth.signOut(),
        new Promise((resolve) => setTimeout(resolve, 1500))
      ])
    } catch {}
    doRedirect()
  }
  const btn = document.getElementById('logoutBtn')
  if (btn) btn.addEventListener('click', (e) => { e.preventDefault(); doLogout() })
  document.addEventListener('click', (e) => {
    const t = e.target.closest && e.target.closest('#logoutBtn')
    if (t) { e.preventDefault(); doLogout() }
  })
})()

window.addEventListener('hashchange', render)

checkAuth().then(render)
