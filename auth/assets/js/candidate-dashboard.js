import { supabase } from './supabase-config.js'
import { backendFetch } from './backend-client.js'

let currentUser = null

// Bootstrap session from URL fragment (access_token/refresh_token) if present, and persist basic info
;(async function bootstrapSessionFromHash() {
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

// Helper: update Applicant Form links with session tokens so the applicant subdomain can set its session
async function updateApplicantLinks() {
  try {
    const linkIds = ['#editDetailsLink', '#applicantFormLink']
    const { data: s } = await supabase.auth.getSession()
    const at = s?.session?.access_token || ''
    const rt = s?.session?.refresh_token || ''
    const uid = currentUser?.id || localStorage.getItem('skreenit_user_id') || ''
    const role = 'candidate'
    const extras = `#access_token=${encodeURIComponent(at)}&refresh_token=${encodeURIComponent(rt)}&user_id=${encodeURIComponent(uid)}&role=${encodeURIComponent(role)}`
    linkIds.forEach(sel => {
      const a = document.querySelector(sel)
      if (a) a.href = `https://applicant.skreenit.com/detailed-application-form.html${extras}`
    })
  } catch {}
}
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
  if (user?.user_metadata?.role !== 'candidate') {
    window.location.href = 'https://login.skreenit.com/login.html'
    throw new Error('Wrong role')
  }
  currentUser = user
  localStorage.setItem('skreenit_user_id', user.id)
  localStorage.setItem('skreenit_role', 'candidate')
  const nameEl = document.querySelector('.user-name') || document.getElementById('candidateName')
  if (nameEl) nameEl.textContent = user.user_metadata?.full_name || 'Candidate'

  // Persist access token for Authorization headers on this subdomain
  try {
    const { data: sessionData } = await supabase.auth.getSession()
    const token = sessionData?.session?.access_token
    if (token) localStorage.setItem('skreenit_token', token)
  } catch {}
  // Now that we have a session, wire applicant links
  updateApplicantLinks()
  return user
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

async function fetchGeneralVideoStatus() {
  try {
    const token = localStorage.getItem('skreenit_token')
    const res = await backendFetch(`/video/general/${currentUser.id}`, {
      headers: {
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      }
    })
    if (!res.ok) return { status: 'missing' }
    return await res.json()
  } catch { return { status: 'missing' } }
}

async function fetchPendingVideoQuestions() {
  try {
    const token = localStorage.getItem('skreenit_token')
    // Find latest application with status under_review for this candidate
    const resp = await backendFetch('/dashboard/summary', {
      headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) },
    })
    const data = await resp.json().catch(() => ({}))
    const apps = data?.applications || []
    const underReview = apps.find(a => a.status === 'under_review')
    if (!underReview) return null
    // Fetch job questions for that application
    const jobId = underReview.job_id
    const q = await backendFetch(`/recruiter/job/${jobId}/questions`, {
      headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) },
    })
    const qData = await q.json().catch(() => ({}))
    return { application: underReview, questions: qData?.questions || [] }
  } catch { return null }
}

function renderOverview(statusData) {
  const banner = statusData?.status !== 'completed' ? `
    <div class="notice" style="background:#fffbea;border:1px solid #f6e05e;color:#975a16;padding:1rem;border-radius:8px;margin-bottom:1rem;">
      <strong>Action needed:</strong> Please complete your General Interview Video below.
    </div>
  ` : ''

  const node = el(`
    <section id="overviewSection" class="dashboard-section">
      <div class="section-header">
        <h1>Dashboard Overview</h1>
      </div>
      ${banner}
      <div class="card" style="background:#fff;border-radius:12px;padding:1rem;box-shadow:0 2px 10px rgba(0,0,0,.06);margin-bottom:1rem;">
        <h3 style="margin-top:0;display:flex;align-items:center;gap:.5rem;"><i class="fas fa-video"></i> General Interview Video</h3>
        <div id="generalVideoStatus">
          ${statusData?.video_url ? `<p><strong>Status:</strong> ${statusData.status || 'uploaded'}</p><video controls style="max-width:100%;height:auto" src="${statusData.video_url}"></video>` : '<p>No video uploaded yet.</p>'}
          ${statusData?.scores ? `<pre style="background:#f7fafc;padding:.75rem;border-radius:8px;">${JSON.stringify(statusData.scores, null, 2)}</pre>` : ''}
        </div>
        <form id="generalVideoForm" style="margin-top:1rem;display:flex;gap:.75rem;align-items:center;flex-wrap:wrap;">
          <input type="file" id="generalVideoInput" accept="video/*" required />
          <button type="submit" class="btn btn-primary">Upload / Replace</button>
      </div>
      <div class="card" style="background:#fff;border-radius:12px;padding:1rem;box-shadow:0 2px 10px rgba(0,0,0,.06);">
        <h3 style="margin-top:0;display:flex;align-items:center;gap:.5rem;"><i class="fas fa-question-circle"></i> Next Stage Video Questions</h3>
        <div id="nextStageContainer"><em>Loading...</em></div>
        <a class="btn btn-primary" id="applicantFormLink" href="#" style="display:block;margin-top:1rem;">View Applicant Form</a>
      </div>
</section>
  `)

  node.querySelector('#generalVideoForm').addEventListener('submit', async (e) => {
    e.preventDefault()
    const file = node.querySelector('#generalVideoInput').files?.[0]
    const token = localStorage.getItem('skreenit_token')
    const user = JSON.parse(localStorage.getItem('skreenit_user') || '{}')
    const link = document.querySelector('#applicantFormLink')
    link.href = `https://applicant.skreenit.com/form.html?access_token=${token}&user_id=${user.id}&email=${user.email}`
    if (!file) return
    const fd = new FormData()
    fd.append('candidate_id', currentUser.id)
    fd.append('video', file)
    try {
      const token = localStorage.getItem('skreenit_token')
      const resp = await backendFetch('/video/general', {
        method: 'POST',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: fd,
      })
      if (!resp.ok) throw new Error('Upload failed')
      const data = await resp.json()
      alert('Video uploaded!')
      render()
    } catch (err) {
      alert('Failed to upload video')
    }
  })

  mountContent(node)
  // ensure applicant link carries tokens
  updateApplicantLinks()

  // Load next-stage questions lazily
  ;(async () => {
    const host = node.querySelector('#nextStageContainer')
    try {
      const pending = await fetchPendingVideoQuestions()
      if (!pending || !(pending.questions || []).length) {
        host.innerHTML = '<span style="color:#718096">No next-stage questions yet.</span>'
        return
      }
      const { application, questions } = pending
      host.innerHTML = `
        <div style="display:grid;gap:.5rem;">
          ${(questions || []).map((q, idx) => `
            <div class="video-response" data-qid="${q.id || idx}">
              <p><strong>Q${q.question_order || (idx + 1)}:</strong> ${q.question_text}</p>
              <div class="video-controls">
                <button class="btn btn-secondary start-rec">Record</button>
                <button class="btn btn-secondary stop-rec" disabled>Stop</button>
                <button class="btn btn-primary upload-rec" disabled>Upload</button>
              </div>
              <video class="preview" style="max-width:100%;height:auto;margin-top:.5rem;" playsinline></video>
            </div>
          `).join('')}
        </div>
      `

      // Minimal WebRTC capture per question
      const blocks = host.querySelectorAll('.video-response')
      blocks.forEach(block => {
        let mediaStream = null
        let recorder = null
        let chunks = []
        const startBtn = block.querySelector('.start-rec')
        const stopBtn = block.querySelector('.stop-rec')
        const uploadBtn = block.querySelector('.upload-rec')
        const videoEl = block.querySelector('video.preview')
        const questionId = block.getAttribute('data-qid')

        startBtn.addEventListener('click', async () => {
          try {
            mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
            videoEl.srcObject = mediaStream
            videoEl.muted = true
            videoEl.play()
            recorder = new MediaRecorder(mediaStream, { mimeType: 'video/webm' })
            chunks = []
            recorder.ondataavailable = (e) => { if (e.data?.size) chunks.push(e.data) }
            recorder.start()
            startBtn.disabled = true
            stopBtn.disabled = false
            uploadBtn.disabled = true
          } catch (e) {
            alert('Could not start recording')
          }
        })

        stopBtn.addEventListener('click', () => {
          try { recorder && recorder.stop() } catch {}
          try { mediaStream && mediaStream.getTracks().forEach(t => t.stop()) } catch {}
          const blob = new Blob(chunks, { type: 'video/webm' })
          videoEl.srcObject = null
          videoEl.src = URL.createObjectURL(blob)
          startBtn.disabled = false
          stopBtn.disabled = true
          uploadBtn.disabled = false
          block._lastBlob = blob
        })

        uploadBtn.addEventListener('click', async () => {
          const blob = block._lastBlob
          if (!blob) return
          try {
            const token = localStorage.getItem('skreenit_token')
            // Reuse existing upload service: save to storage and DB via backend /video
            const fd = new FormData()
            fd.append('candidate_id', currentUser.id)
            fd.append('application_id', pending.application.id)
            fd.append('question_id', questionId)
            fd.append('video', blob, `response-${questionId}.webm`)
            const resp = await backendFetch('/video/general', { // temporary unified endpoint in backend/video.py
              method: 'POST',
              headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) },
              body: fd,
            })
            if (!resp.ok) throw new Error('Upload failed')
            alert('Response uploaded')
          } catch (e) {
            alert('Failed to upload response')
          }
        })
      })
    } catch (e) {
      host.innerHTML = '<span style="color:#e53e3e">Failed to load questions</span>'
    }
  })()
}

function renderJobs() {
  const node = el(`
    <section class="dashboard-section">
      <div class="section-header"><h1>Job Search</h1></div>
      <div class="card" style="background:#fff;border-radius:12px;padding:1rem;box-shadow:0 2px 10px rgba(0,0,0,.06);">
        <div style="display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:.75rem;">
          <input type="text" id="jobQuery" placeholder="Search jobs by title, company, skills" style="flex:1;min-width:220px;">
          <button class="btn btn-primary" id="jobSearchBtn">Search</button>
        </div>
        <div id="jobResults"><em>Loading jobs...</em></div>
      </div>
    </section>
  `)
  mountContent(node)
  const results = node.querySelector('#jobResults')
  ;(async () => {
    try {
      const token = localStorage.getItem('skreenit_token')
      const resp = await backendFetch('/dashboard/summary', { headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) } })
      const data = await resp.json().catch(() => ({}))
      const jobs = data?.jobs || []
      if (!jobs.length) { results.innerHTML = '<span style="color:#718096">No jobs available right now.</span>'; return }
      results.innerHTML = `
        <div style="display:grid;gap:.75rem;">
          ${jobs.map(j => `
            <div class="card" style="padding:.75rem;border:1px solid #e2e8f0;border-radius:8px;">
              <div style="display:flex;justify-content:space-between;align-items:center;gap:.5rem;flex-wrap:wrap;">
                <div>
                  <div style="font-weight:600;">${j.title || 'Job'}</div>
                  <div style="font-size:.9rem;color:#4a5568;">${j.company || ''}</div>
                </div>
                <button class="btn btn-secondary" data-job-id="${j.id}">View</button>
              </div>
            </div>
          `).join('')}
        </div>
      `
    } catch { results.innerHTML = '<span style="color:#e53e3e">Failed to load jobs</span>' }
  })()
}

function renderApplications() {
  const node = el(`
    <section class="dashboard-section">
      <div class="section-header"><h1>My Applications</h1></div>
      <div id="appsHost" class="card" style="background:#fff;border-radius:12px;padding:1rem;box-shadow:0 2px 10px rgba(0,0,0,.06);"></div>
    </section>
  `)
  mountContent(node)
  const host = node.querySelector('#appsHost')
  ;(async () => {
    try {
      const token = localStorage.getItem('skreenit_token')
      const resp = await fetch(`${BACKEND_URL}/dashboard/summary`, { headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) } })
      const data = await resp.json().catch(() => ({}))
      const apps = data?.applications || []
      if (!apps.length) { host.innerHTML = '<span style="color:#718096">No applications yet.</span>'; return }
      host.innerHTML = `
        <div style="display:grid;gap:.75rem;">
          ${apps.map(a => `
            <div class="card" style="padding:.75rem;border:1px solid #e2e8f0;border-radius:8px;">
              <div style="display:flex;justify-content:space-between;align-items:center;gap:.5rem;flex-wrap:wrap;">
                <div>
                  <div style="font-weight:600;">${a.job_title || 'Job'}</div>
                  <div style="font-size:.9rem;color:#4a5568;">Status: ${a.status || 'submitted'}</div>
                </div>
                <a class="btn btn-secondary" href="#overview">View</a>
              </div>
            </div>
          `).join('')}
        </div>
      `
    } catch { host.innerHTML = '<span style="color:#e53e3e">Failed to load applications</span>' }
  })()
}

function renderProfile() {
  const node = el(`
    <section class="dashboard-section">
      <div class="section-header"><h1>Your Profile</h1></div>
      <div class="card" style="background:#fff;border-radius:12px;padding:1rem;box-shadow:0 2px 10px rgba(0,0,0,.06);display:grid;gap:1rem;">
        <form id="profileView" class="form" onsubmit="return false;" style="display:grid;gap:.75rem;">
          <div class="form-row">
            <div class="form-group">
              <label>First Name</label>
              <input type="text" id="pv_firstName" readonly>
            </div>
            <div class="form-group">
              <label>Last Name</label>
              <input type="text" id="pv_lastName" readonly>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Email</label>
              <input type="email" id="pv_email" readonly>
            </div>
            <div class="form-group">
              <label>Phone</label>
              <input type="text" id="pv_phone" readonly>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group"><label>City</label><input type="text" id="pv_city" readonly></div>
            <div class="form-group"><label>State</label><input type="text" id="pv_state" readonly></div>
            <div class="form-group"><label>Country</label><input type="text" id="pv_country" readonly></div>
          </div>
        </form>
        <div style="display:flex;gap:.5rem;flex-wrap:wrap;">
          <a class="btn btn-secondary" id="editDetailsLink" href="https://applicant.skreenit.com/detailed-application-form.html">Edit/Update Details</a>
          <button class="btn" id="refreshResumeBtn">Refresh Resume Preview</button>
        </div>
        <div>
          <h3 style="margin:0 0 .5rem 0;display:flex;align-items:center;gap:.5rem;"><i class="fas fa-file"></i> Resume</h3>
          <div id="resumeBox" style="background:#f7fafc;border:1px dashed #cbd5e0;border-radius:8px;padding:.75rem;min-height:48px;display:flex;justify-content:space-between;align-items:center;gap:.5rem;flex-wrap:wrap;">
            <span id="resumeStatus" style="color:#718096">No resume found</span>
            <a id="resumeLink" class="btn btn-secondary" target="_blank" style="display:none;">Open</a>
          </div>
          <form id="resumeUploadForm" style="margin-top:.5rem;display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;">
            <input type="file" id="resumeFile" accept=".pdf,.doc,.docx,.rtf,.txt,.odt" />
            <button type="submit" class="btn btn-primary">Upload New Resume</button>
          </form>
        </div>
      </div>
    </section>
  `)
  mountContent(node)

  // Prefill readonly form from backend detailed form
  ;(async () => {
    try {
      const token = localStorage.getItem('skreenit_token')
      const res = await backendFetch(`/applicant/detailed-form/${currentUser.id}`, {
        headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) }
      })
      if (res.ok) {
        const data = await res.json()
        const p = data.profile || {}
        const set = (id, v) => { const el = node.querySelector('#' + id); if (el) el.value = v || '' }
        set('pv_firstName', p.first_name)
        set('pv_lastName', p.last_name)
        set('pv_email', p.email || (currentUser.email || ''))
        set('pv_phone', p.phone)
        set('pv_city', p.city)
        set('pv_state', p.state)
        set('pv_country', p.country)
      } else {
        // fallback minimal
        const set = (id, v) => { const el = node.querySelector('#' + id); if (el) el.value = v || '' }
        const meta = currentUser?.user_metadata || {}
        const [fn, ln] = (meta.full_name || '').split(' ')
        set('pv_firstName', fn)
        set('pv_lastName', ln)
        set('pv_email', currentUser.email || '')
      }
    } catch {}
  })()

  // ensure applicant link carries tokens
  updateApplicantLinks()

  async function loadResume() {
    const status = node.querySelector('#resumeStatus')
    const link = node.querySelector('#resumeLink')
    try {
      const token = localStorage.getItem('skreenit_token')
      const resp = await backendFetch(`/applicant/resume-url/${currentUser.id}`, { headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) } })
      if (!resp.ok) throw new Error('not found')
      const data = await resp.json()
      status.textContent = 'Latest resume available'
      link.href = data.resume_url
      link.style.display = 'inline-block'
    } catch {
      status.textContent = 'No resume found'
      link.style.display = 'none'
      link.removeAttribute('href')
    }
  }

  node.querySelector('#refreshResumeBtn').addEventListener('click', loadResume)
  node.querySelector('#resumeUploadForm').addEventListener('submit', async (e) => {
    e.preventDefault()
    const f = node.querySelector('#resumeFile')
    const file = f?.files?.[0]
    if (!file) return alert('Choose a file')
    try {
      const fd = new FormData()
      fd.append('applicant_id', currentUser.id)
      fd.append('resume', file)
      const token = localStorage.getItem('skreenit_token')
      const resp = await backendFetch('/applicant/upload-resume', {
        method: 'POST',
        headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) },
        body: fd,
      })
      if (!resp.ok) throw new Error('Upload failed')
      alert('Resume uploaded')
      await loadResume()
    } catch { alert('Failed to upload resume') }
  })

  loadResume()
}

async function render() {
  const hash = window.location.hash || '#overview'
  setActiveNav(hash)
  if (hash === '#profile') return renderProfile()
  if (hash === '#jobs') return renderJobs()
  if (hash === '#applications') return renderApplications()
  const status = await fetchGeneralVideoStatus()
  return renderOverview(status)
}

window.addEventListener('hashchange', render)

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
      // Clear local session info immediately
      try {
        localStorage.removeItem('skreenit_token')
        localStorage.removeItem('skreenit_refresh_token')
        localStorage.removeItem('skreenit_user_id')
        localStorage.removeItem('skreenit_role')
      } catch {}
      // Try Supabase sign out with timeout fallback
      await Promise.race([
        supabase.auth.signOut(),
        new Promise((resolve) => setTimeout(resolve, 1500))
      ])
    } catch {}
    doRedirect()
  }
  const btn = document.getElementById('logoutBtn')
  if (btn) btn.addEventListener('click', (e) => { e.preventDefault(); doLogout() })
  // Delegated fallback
  document.addEventListener('click', (e) => {
    const t = e.target.closest && e.target.closest('#logoutBtn')
    if (t) { e.preventDefault(); doLogout() }
  })
})()

checkAuth().then(render)
