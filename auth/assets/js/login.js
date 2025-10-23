document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('loginForm');
  const formError = document.getElementById('formError');
  const roleInput = document.getElementById('role');
  const roleOptions = document.querySelectorAll('.role-option');
  const recruiterBox = document.getElementById('recruiterBox');
  const submitButton = form.querySelector('button[type="submit"]');
  const buttonText = submitButton.querySelector('.button-text');
  
  // Role selection handling
  roleOptions.forEach(option => {
    option.addEventListener('click', () => {
      const selectedRole = option.dataset.role;
      
      // Update UI
      roleOptions.forEach(opt => opt.classList.remove('selected'));
      option.classList.add('selected');
      
      // Update hidden input
      roleInput.value = selectedRole;
      
      // Show/hide recruiter fields
      if (recruiterBox) {
        recruiterBox.style.display = selectedRole === 'recruiter' ? 'block' : 'none';
        const companyIdInput = recruiterBox.querySelector('input');
        if (companyIdInput) {
          companyIdInput.required = selectedRole === 'recruiter';
        }
      }
    });
  });
  
  // Form submission
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Clear previous error
    formError.style.display = 'none';
    formError.textContent = '';
    
    // Validate role selection
    if (!roleInput.value) {
      showError('Please select your role');
      return;
    }
    
    // Update button state
    submitButton.disabled = true;
    buttonText.textContent = 'Signing in...';
    
    try {
      const formData = new FormData(form);
      const role = formData.get('role');
      const email = formData.get('email');
      const password = formData.get('password');
      const companyId = formData.get('company_id');
      
      // Validate company ID for recruiters
      if (role === 'recruiter' && !companyId) {
        throw new Error('Company ID is required for recruiter login');
      }
      
      // Sign in with Supabase
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });
      
      if (error) throw error;
      
      // Verify role matches
      const userRole = data.user?.user_metadata?.role;
      if (userRole !== role) {
        await supabase.auth.signOut();
        throw new Error(`Invalid role. Please sign in as ${userRole}`);
      }
      
      // Verify company ID for recruiters
      if (role === 'recruiter') {
        const userCompanyId = data.user?.user_metadata?.company_id;
        if (companyId !== userCompanyId) {
          await supabase.auth.signOut();
          throw new Error('Invalid Company ID');
        }
      }
      
      // Store session data
      const session = data.session;
      if (session) {
        localStorage.setItem('skreenit_token', session.access_token);
        localStorage.setItem('skreenit_refresh_token', session.refresh_token);
        localStorage.setItem('skreenit_user_id', data.user.id);
        localStorage.setItem('skreenit_role', role);
      }
      
      // Check first-time login status
      const isFirstTimeLogin = data.user?.user_metadata?.first_time_login === true;
      const hasUpdatedPassword = data.user?.user_metadata?.password_updated === true;
      
      // Handle redirects
      if (!hasUpdatedPassword) {
        window.location.href = 'https://login.skreenit.com/update-password.html';
      } else if (role === 'recruiter') {
        if (isFirstTimeLogin) {
          window.location.href = 'https://recruiter.skreenit.com/recruiter-profile.html';
        } else {
          window.location.href = 'https://dashboard.skreenit.com/recruiter-dashboard.html';
        }
      } else {
        if (isFirstTimeLogin) {
          window.location.href = 'https://applicant.skreenit.com/detailed-application-form.html';
        } else {
          window.location.href = 'https://dashboard.skreenit.com/candidate-dashboard.html';
        }
      }
      
    } catch (error) {
      showError(error.message || 'Login failed');
    } finally {
      submitButton.disabled = false;
      buttonText.textContent = 'Sign In';
    }
  });
  
  function showError(message) {
    formError.textContent = message;
    formError.style.display = 'block';
    formError.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
  
  // Add password visibility toggle
  const passwordInput = document.getElementById('password');
  if (passwordInput) {
    const toggleButton = document.createElement('button');
    toggleButton.type = 'button';
    toggleButton.className = 'password-toggle';
    toggleButton.innerHTML = '<i class="fas fa-eye"></i>';
    toggleButton.style.position = 'absolute';
    toggleButton.style.right = '1rem';
    toggleButton.style.top = '50%';
    toggleButton.style.transform = 'translateY(-50%)';
    toggleButton.style.background = 'none';
    toggleButton.style.border = 'none';
    toggleButton.style.cursor = 'pointer';
    toggleButton.style.color = 'var(--text-light)';
    
    const passwordWrapper = document.createElement('div');
    passwordWrapper.style.position = 'relative';
    passwordInput.parentNode.insertBefore(passwordWrapper, passwordInput);
    passwordWrapper.appendChild(passwordInput);
    passwordWrapper.appendChild(toggleButton);
    
    toggleButton.addEventListener('click', () => {
      const type = passwordInput.type === 'password' ? 'text' : 'password';
      passwordInput.type = type;
      toggleButton.innerHTML = type === 'password' ? 
        '<i class="fas fa-eye"></i>' : 
        '<i class="fas fa-eye-slash"></i>';
    });
  }
});