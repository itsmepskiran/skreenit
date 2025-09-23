import { supabase } from './supabase-config.js'

const BACKEND_URL = window.SKREENIT_BACKEND_URL || 'https://skreenit-api.onrender.com'
let currentUser = null

function qs(sel) { return document.querySelector(sel) }
function el(html) { const d = document.createElement('div'); d.innerHTML = html.trim(); return d.firstChild }

async function checkAuth() {
  const { data, error } = await supabase.auth.getUser()
  if (error || !data?.user) {
    window.location.href = 'https://login.skreenit.com/'
    throw new Error('Not authenticated')
  }
  const user = data.user
  if (user?.user_metadata?.role !== 'recruiter') {
    window.location.href = 'https://login.skreenit.com/'
    throw new Error('Wrong role')
  }
  currentUser = user
  localStorage.setItem('skreenit_user_id', user.id)
  localStorage.setItem('skreenit_role', 'recruiter')
  const nameEl = document.querySelector('.user-name')
  if (nameEl) nameEl.textContent = user.user_metadata?.full_name || 'Recruiter'
}

function mountContent(node) {
  const main = qs('.main-content')
  if (!main) return
  main.innerHTML = ''
  main.appendChild(node)
}

function renderOverview() {
  const node = el(`
    <section id="overviewSection" class="dashboard-section">
      <div class="section-header">
        <h1>Dashboard Overview</h1>
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
    </section>
  `)

  node.querySelector('#approveForm').addEventListener('submit', async (e) => {
    e.preventDefault()
    const appId = node.querySelector('#applicationIdInput').value.trim()
    if (!appId) return
    try {
      const resp = await fetch(`${BACKEND_URL}/recruiter/application/${appId}/approve`, { method: 'POST' })
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
      const resp = await fetch(`${BACKEND_URL}/recruiter/application/${appId}/resume-url`)
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
      const resp = await fetch(`${BACKEND_URL}/recruiter/job/${jobId}/questions`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
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
      const resp = await fetch(`${BACKEND_URL}/recruiter/job/${jobId}/questions`)
      const data = await resp.json()
      if (!resp.ok) throw new Error(data?.detail || 'Fetch failed')
      listEl.innerHTML = '<ol>' + (data.questions || []).map(q => `<li>${q.question_text}</li>`).join('') + '</ol>'
    } catch (err) {
      listEl.textContent = 'Failed to load questions'
    }
  })

  mountContent(node)
}

checkAuth().then(renderOverview)
