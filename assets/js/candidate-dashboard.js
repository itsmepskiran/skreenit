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
  if (user?.user_metadata?.role !== 'candidate') {
    window.location.href = 'https://login.skreenit.com/'
    throw new Error('Wrong role')
  }
  currentUser = user
  localStorage.setItem('skreenit_user_id', user.id)
  localStorage.setItem('skreenit_role', 'candidate')
  const nameEl = document.querySelector('.user-name')
  if (nameEl) nameEl.textContent = user.user_metadata?.full_name || 'Candidate'

  // Persist access token for Authorization headers on this subdomain
  try {
    const { data: sessionData } = await supabase.auth.getSession()
    const token = sessionData?.session?.access_token
    if (token) localStorage.setItem('skreenit_token', token)
  } catch {}
  return user
}

function mountContent(node) {
  const main = qs('.main-content')
  if (!main) return
  main.innerHTML = ''
  main.appendChild(node)
}

async function fetchGeneralVideoStatus() {
  try {
    const token = localStorage.getItem('skreenit_token')
    const res = await fetch(`${BACKEND_URL}/applicant/general-video/${currentUser.id}`, {
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
    const resp = await fetch(`${BACKEND_URL}/dashboard/summary`, {
      headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) },
    })
    const data = await resp.json().catch(() => ({}))
    const apps = data?.applications || []
    const underReview = apps.find(a => a.status === 'under_review')
    if (!underReview) return null
    // Fetch job questions for that application
    const jobId = underReview.job_id
    const q = await fetch(`${BACKEND_URL}/recruiter/job/${jobId}/questions`, {
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
        </form>
      </div>
      <div class="card" style="background:#fff;border-radius:12px;padding:1rem;box-shadow:0 2px 10px rgba(0,0,0,.06);">
        <h3 style="margin-top:0;display:flex;align-items:center;gap:.5rem;"><i class="fas fa-question-circle"></i> Next Stage Video Questions</h3>
        <div id="nextStageContainer"><em>Loading...</em></div>
      </div>
    </section>
  `)

  node.querySelector('#generalVideoForm').addEventListener('submit', async (e) => {
    e.preventDefault()
    const file = node.querySelector('#generalVideoInput').files?.[0]
    if (!file) return
    const fd = new FormData()
    fd.append('candidate_id', currentUser.id)
    fd.append('video', file)
    try {
      const token = localStorage.getItem('skreenit_token')
      const resp = await fetch(`${BACKEND_URL}/applicant/general-video`, {
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
            const resp = await fetch(`${BACKEND_URL}/video/general`, { // temporary unified endpoint in backend/video.py
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

function renderProfile() {
  const profile = currentUser?.user_metadata || {}
  const node = el(`
    <section class="dashboard-section">
      <div class="section-header"><h1>Your Profile</h1></div>
      <div class="card" style="background:#fff;border-radius:12px;padding:1rem;box-shadow:0 2px 10px rgba(0,0,0,.06);">
        <p><strong>Name:</strong> ${profile.full_name || ''}</p>
        <p><strong>Email:</strong> ${currentUser.email || ''}</p>
        <p><strong>Mobile:</strong> ${profile.mobile || ''}</p>
        <p><strong>Location:</strong> ${profile.location || ''}</p>
      </div>
    </section>
  `)
  mountContent(node)
}

async function render() {
  const hash = window.location.hash || '#overview'
  if (hash === '#profile') return renderProfile()
  const status = await fetchGeneralVideoStatus()
  return renderOverview(status)
}

window.addEventListener('hashchange', render)

checkAuth().then(render)
