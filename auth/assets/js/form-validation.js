// Password validation rules
const passwordRules = {
  minLength: 8,
  hasLetter: /[a-zA-Z]/,
  hasNumber: /\d/,
  hasSpecial: /[!@#$%^&*]/
};

// Validate password strength
export function validatePassword(password) {
  const errors = [];
  
  if (password.length < passwordRules.minLength) {
    errors.push('Password must be at least 8 characters long');
  }
  if (!passwordRules.hasLetter.test(password)) {
    errors.push('Password must contain at least one letter');
  }
  if (!passwordRules.hasNumber.test(password)) {
    errors.push('Password must contain at least one number');
  }
  if (!passwordRules.hasSpecial.test(password)) {
    errors.push('Password must contain at least one special character');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
}

// Live password strength indicator
export function setupPasswordStrengthIndicator(passwordInput, strengthIndicator) {
  passwordInput.addEventListener('input', () => {
    const password = passwordInput.value;
    const validation = validatePassword(password);
    
    // Update strength indicator
    if (password.length === 0) {
      strengthIndicator.className = 'password-strength';
      strengthIndicator.textContent = '';
    } else if (validation.isValid) {
      strengthIndicator.className = 'password-strength strong';
      strengthIndicator.textContent = '💪 Strong password';
    } else if (password.length >= 6 && validation.errors.length <= 2) {
      strengthIndicator.className = 'password-strength medium';
      strengthIndicator.textContent = '👍 Medium strength';
    } else {
      strengthIndicator.className = 'password-strength weak';
      strengthIndicator.textContent = '⚠️ Weak password';
    }
  });
}

// Setup form validation
export function setupFormValidation(form, options = {}) {
  const inputs = form.querySelectorAll('input, select, textarea');
  
  inputs.forEach(input => {
    // Add validation classes on blur
    input.addEventListener('blur', () => {
      const formGroup = input.closest('.form-group');
      if (!formGroup) return;
      
      if (input.checkValidity()) {
        formGroup.classList.add('valid');
        formGroup.classList.remove('invalid');
      } else if (input.value) {
        formGroup.classList.add('invalid');
        formGroup.classList.remove('valid');
      }
    });
    
    // Remove validation classes on input
    input.addEventListener('input', () => {
      const formGroup = input.closest('.form-group');
      if (!formGroup) return;
      formGroup.classList.remove('valid', 'invalid');
    });
  });
  
  // Password confirmation validation
  const password = form.querySelector('input[type="password"][id="password"]');
  const confirmPassword = form.querySelector('input[type="password"][id="confirm_password"]');
  
  if (password && confirmPassword) {
    confirmPassword.addEventListener('input', () => {
      if (password.value !== confirmPassword.value) {
        confirmPassword.setCustomValidity("Passwords don't match");
      } else {
        confirmPassword.setCustomValidity('');
      }
    });
    
    password.addEventListener('input', () => {
      if (confirmPassword.value) {
        if (password.value !== confirmPassword.value) {
          confirmPassword.setCustomValidity("Passwords don't match");
        } else {
          confirmPassword.setCustomValidity('');
        }
      }
    });
  }
  
  // Role-specific fields
  const roleSelect = form.querySelector('select[name="role"]');
  if (roleSelect) {
    const recruiterFields = document.getElementById('recruiterFields');
    const candidateFields = document.getElementById('candidateFields');
    
    roleSelect.addEventListener('change', () => {
      if (recruiterFields) {
        recruiterFields.classList.toggle('hidden', roleSelect.value !== 'recruiter');
        
        // Update required attributes
        recruiterFields.querySelectorAll('input').forEach(input => {
          input.required = roleSelect.value === 'recruiter';
        });
      }
      
      if (candidateFields) {
        candidateFields.classList.toggle('hidden', roleSelect.value !== 'candidate');
      }
    });
  }
  
  // Form submission handling
  if (options.onSubmit) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      // Validate all fields
      let isValid = true;
      inputs.forEach(input => {
        if (!input.checkValidity()) {
          isValid = false;
          const formGroup = input.closest('.form-group');
          if (formGroup) {
            formGroup.classList.add('invalid');
          }
        }
      });
      
      if (!isValid) {
        return;
      }
      
      // Call onSubmit handler
      try {
        await options.onSubmit(e);
      } catch (error) {
        console.error('Form submission error:', error);
      }
    });
  }
}