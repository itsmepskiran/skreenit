// Shared Detailed Application Form logic - hosted under auth/assets for cross-subdomain use
import { supabase } from './supabase-config.js'

const form = document.getElementById('detailedApplicationForm')
const prevBtn = document.getElementById('prevBtn')
const nextBtn = document.getElementById('nextBtn')
const submitBtn = document.getElementById('submitBtn')
const progressFill = document.getElementById('progressFill')
const saveDraftBtn = document.getElementById('saveDraftBtn')
const logoutBtn = document.getElementById('logoutBtn')

let currentStep = 1
const totalSteps = 6

function updateUI() {
  document.querySelectorAll('.form-step').forEach(step => {
    const s = Number(step.dataset.step)
    step.classList.toggle('active', s === currentStep)
    step.style.display = s === currentStep ? 'block' : 'none'
  })
  document.querySelectorAll('.step').forEach(el => {
    const s = Number(el.dataset.step)
    el.classList.toggle('active', s === currentStep)
  })
  if (prevBtn) prevBtn.style.display = currentStep > 1 ? 'inline-flex' : 'none'
  if (nextBtn) nextBtn.style.display = currentStep < totalSteps ? 'inline-flex' : 'none'
  if (submitBtn) submitBtn.style.display = currentStep === totalSteps ? 'inline-flex' : 'none'
  if (progressFill) progressFill.style.width = `${Math.round(((currentStep-1)/(totalSteps-1))*100)}%`
}

prevBtn?.addEventListener('click', () => { if (currentStep>1) { currentStep--; updateUI() } })
nextBtn?.addEventListener('click', () => { if (currentStep<totalSteps) { currentStep++; updateUI() } })

function serializeForm(formEl) {
  const data = {}
  const formData = new FormData(formEl)
  for (const [key, value] of formData.entries()) {
    if (value instanceof File) continue
    if (data[key]) {
      if (!Array.isArray(data[key])) data[key] = [data[key]]
      data[key].push(value)
    } else {
      data[key] = value
    }
  }
  return data
}

async function uploadFileIfAny(inputId, folder, userId) {
  const input = document.getElementById(inputId)
  if (!input || !input.files || input.files.length === 0) return null
  const file = input.files[0]
  const path = `${userId}/${folder}/${Date.now()}-${file.name}`
  const { error } = await supabase.storage.from('applications').upload(path, file)
  if (error) throw error
  const { data } = supabase.storage.from('applications').getPublicUrl(path)
  return data.publicUrl
}

async function requireUser() {
  const { data, error } = await supabase.auth.getUser()
  if (error || !data?.user) {
    window.location.href = 'https://auth.skreenit.com/login.html'
    return null
  }
  return data.user
}

async function saveDraft() {
  const user = await requireUser()
  if (!user) return
  const payload = serializeForm(form)
  // Optional uploads in Documents step
  try {
    const resumeUrl = await uploadFileIfAny('resume', 'resume', user.id)
    if (resumeUrl) payload.resumeUrl = resumeUrl
    const coverUrl = await uploadFileIfAny('coverLetter', 'cover', user.id)
    if (coverUrl) payload.coverLetterUrl = coverUrl
  } catch (e) {
    console.warn('Upload failed (draft continues):', e)
  }
  const { error } = await supabase.from('candidate_form_drafts').upsert({
    user_id: user.id,
    data: payload,
    status: 'draft',
    updated_at: new Date().toISOString()
  }, { onConflict: 'user_id' })
  if (error) throw error
  alert('Draft saved successfully')
}

async function submitApplication() {
  const user = await requireUser()
  if (!user) return false
  const payload = serializeForm(form)

  // Ensure email field is set to user.email if present
  if (!payload.email) payload.email = user.email

  // Upload files (replace or add)
  try {
    const resumeUrl = await uploadFileIfAny('resume', 'resume', user.id)
    if (resumeUrl) payload.resumeUrl = resumeUrl
    const coverUrl = await uploadFileIfAny('coverLetter', 'cover', user.id)
    if (coverUrl) payload.coverLetterUrl = coverUrl
  } catch (e) {
    console.warn('Upload failed:', e)
  }

  // Insert application record
  const { error } = await supabase.from('candidate_applications').insert({
    user_id: user.id,
    data: payload,
    status: 'submitted',
    submitted_at: new Date().toISOString()
  })
  if (error) {
    alert('Submission failed. Please try again.')
    console.error(error)
    return false
  }
  return true
}

form?.addEventListener('submit', async (e) => {
  e.preventDefault()
  const ok = await submitApplication()
  if (!ok) return
  const modal = document.getElementById('successModal')
  if (modal) {
    modal.style.display = 'block'
  } else {
    window.location.href = 'https://dashboards.skreenit.com/candidate-dashboard.html'
  }
})

saveDraftBtn?.addEventListener('click', async () => {
  try { await saveDraft() } catch (e) { alert('Could not save draft'); console.error(e) }
})

logoutBtn?.addEventListener('click', () => window.location.href = 'https://auth.skreenit.com/login.html')

updateUI()
