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
    const res = await fetch(`${BACKEND_URL}/applicant/general-video/${currentUser.id}`)
    if (!res.ok) return { status: 'missing' }
    return await res.json()
  } catch { return { status: 'missing' } }
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
      const resp = await fetch(`${BACKEND_URL}/applicant/general-video`, { method: 'POST', body: fd })
      if (!resp.ok) throw new Error('Upload failed')
      const data = await resp.json()
      alert('Video uploaded!')
      render()
    } catch (err) {
      alert('Failed to upload video')
    }
  })

  mountContent(node)
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
