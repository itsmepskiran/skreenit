// Detailed Application Form logic (Shared)
// Minimal stepper and submission logic with redirect to dashboards

const form = document.getElementById('detailedApplicationForm')
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

form?.addEventListener('submit', (e) => {
  e.preventDefault()
  const modal = document.getElementById('successModal')
  if (modal) {
    modal.style.display = 'block'
  } else {
    window.location.href = 'https://dashboards.skreenit.com/candidate-dashboard.html'
  }
})

// Save draft/logout placeholders
const saveDraftBtn = document.getElementById('saveDraftBtn')
const logoutBtn = document.getElementById('logoutBtn')
saveDraftBtn?.addEventListener('click', () => alert('Draft saved (placeholder).'))
logoutBtn?.addEventListener('click', () => window.location.href = 'https://auth.skreenit.com/login.html')

updateUI()
