// Detailed Application Form logic (Shared)
// Minimal stepper and submission logic with redirect to dashboards

const form = document.getElementById('detailedApplicationForm')
const BACKEND_URL = window.SKREENIT_BACKEND_URL || 'https://skreenit-api.onrender.com'
const prevBtn = document.getElementById('prevBtn')
const nextBtn = document.getElementById('nextBtn')
const submitBtn = document.getElementById('submitBtn')
const progressFill = document.getElementById('progressFill')

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

form?.addEventListener('submit', async (e) => {
  e.preventDefault()
  const userId = localStorage.getItem('skreenit_user_id')
  
  // Helpers to serialize repeated sections when available
  function serializeEducation() {
    const container = document.getElementById('educationContainer')
    if (!container) return []
    const items = []
    const entries = container.querySelectorAll('.education-entry, .education-item, [data-education]')
    if (entries.length) {
      entries.forEach((row) => {
        const get = (sel) => row.querySelector(sel)?.value?.trim() || null
        items.push({
          institution: get('[name="institution"], .institution, [data-field="institution"]'),
          degree: get('[name="degree"], .degree, [data-field="degree"]'),
          field_of_study: get('[name="field_of_study"], .field_of_study, [data-field="field_of_study"]'),
          start_date: get('[name="start_date"], .start_date, [data-field="start_date"]'),
          end_date: get('[name="end_date"], .end_date, [data-field="end_date"]'),
          grade: get('[name="grade"], .grade, [data-field="grade"]'),
        })
      })
      return items.filter(x => x.institution && x.degree)
    }
    return []
  }

  function serializeExperience() {
    const container = document.getElementById('experienceContainer')
    if (!container) return []
    const items = []
    const entries = container.querySelectorAll('.experience-entry, .experience-item, [data-experience]')
    if (entries.length) {
      entries.forEach((row) => {
        const get = (sel) => row.querySelector(sel)?.value?.trim() || null
        const isCurrentEl = row.querySelector('[name="is_current"], .is_current, [data-field="is_current"]')
        const is_current = isCurrentEl ? (isCurrentEl.type === 'checkbox' ? isCurrentEl.checked : (isCurrentEl.value === 'true')) : false
        items.push({
          company_name: get('[name="company_name"], .company_name, [data-field="company_name"]'),
          position: get('[name="position"], .position, [data-field="position"]'),
          description: get('[name="description"], .description, [data-field="description"]'),
          start_date: get('[name="start_date"], .start_date, [data-field="start_date"]'),
          end_date: get('[name="end_date"], .end_date, [data-field="end_date"]'),
          is_current,
        })
      })
      return items.filter(x => x.company_name && x.position)
    }
    return []
  }

  function serializeSkills() {
    const container = document.getElementById('skillsContainer') || document.getElementById('skillsSection')
    if (!container) return []
    const items = []
    const entries = container.querySelectorAll('.skill-entry, .skill-item, [data-skill]')
    if (entries.length) {
      entries.forEach((row) => {
        const get = (sel) => row.querySelector(sel)?.value?.trim() || null
        const years = get('[name="years_experience"], .years_experience, [data-field="years_experience"]')
        items.push({
          skill_name: get('[name="skill_name"], .skill_name, [data-field="skill_name"]') || get('input'),
          proficiency_level: get('[name="proficiency_level"], .proficiency_level, [data-field="proficiency_level"]'),
          years_experience: years ? Number(years) : null,
        })
      })
      return items.filter(x => x.skill_name)
    }
    return []
  }
  // Collect a minimal profile subset; backend supports richer payloads
  const payload = {
    candidate_id: userId,
    profile: {
      id: userId,
      email: document.getElementById('email')?.value || null,
      phone: document.getElementById('phone')?.value || null,
      first_name: document.getElementById('firstName')?.value || null,
      last_name: document.getElementById('lastName')?.value || null,
      city: document.getElementById('city')?.value || null,
      state: document.getElementById('state')?.value || null,
      country: document.getElementById('country')?.value || null,
    },
    education: serializeEducation(),
    experience: serializeExperience(),
    skills: serializeSkills(),
  }

  try {
    await fetch(`${BACKEND_URL}/applicant/detailed-form`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  } catch (err) {
    console.warn('Save detailed form failed (non-blocking):', err)
  }

  const modal = document.getElementById('successModal')
  if (modal) {
    modal.style.display = 'block'
  } else {
    window.location.href = 'https://dashboard.skreenit.com/candidate-dashboard.html'
  }
})

// Save draft/logout placeholders
const saveDraftBtn = document.getElementById('saveDraftBtn')
const logoutBtn = document.getElementById('logoutBtn')
saveDraftBtn?.addEventListener('click', () => {
  // Placeholder: persist draft via API/localStorage if needed
  alert('Draft saved (placeholder).')
  // Stay on the same page
})
logoutBtn?.addEventListener('click', () => {
  window.location.href = 'https://login.skreenit.com/'
})

updateUI()
