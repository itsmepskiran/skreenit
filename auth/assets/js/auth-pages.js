// Authentication Pages Handler for Skreenit
// Handles registration, login, and password reset functionality

import { supabase, auth } from './supabase-config.js'
import { backendFetch, handleResponse } from './backend-client.js'

// Registration form handler
export async function handleRegistrationSubmit(event) {
    event.preventDefault()

    const form = event.target
    const submitBtn = form.querySelector('button[type="submit"]')
    const originalText = submitBtn.textContent

    submitBtn.textContent = 'Creating Account...'
    submitBtn.disabled = true

    try {
        const formData = new FormData(form)
        const registrationData = {
            full_name: formData.get('full_name'),
            email: formData.get('email'),
            mobile: formData.get('mobile'),
            location: formData.get('location'),
            role: formData.get('role'),
            company_name: formData.get('company_name'),
            resume: formData.get('resume')
        }

        const requiredFields = ['full_name', 'email', 'mobile', 'location', 'role']
        for (const field of requiredFields) {
            if (!registrationData[field]) {
                throw new Error(`${field.replace('_', ' ')} is required`)
            }
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        if (!emailRegex.test(registrationData.email)) {
            throw new Error('Please enter a valid email address')
        }

        if (registrationData.mobile.length < 10) {
            throw new Error('Please enter a valid mobile number')
        }

        console.log('Registering with Supabase...')
        const { data: authData, error: authError } = await auth.signUp(
            registrationData.email,
            formData.get('password'),
            {
                data: {
                    full_name: registrationData.full_name,
                    role: registrationData.role,
                    mobile: registrationData.mobile,
                    location: registrationData.location
                }
            }
        )

        if (authError) {
            throw new Error(`Registration failed: ${authError.message}`)
        }

        console.log('Supabase registration successful')

        const backendFormData = new FormData()
        backendFormData.append('full_name', registrationData.full_name)
        backendFormData.append('email', registrationData.email)
        backendFormData.append('mobile', registrationData.mobile)
        backendFormData.append('location', registrationData.location)
        backendFormData.append('role', registrationData.role)
        backendFormData.append('company_name', registrationData.company_name || '')

        const resumeFile = formData.get('resume')
        if (resumeFile && resumeFile.size > 0) {
            backendFormData.append('resume', resumeFile)
        }

        const response = await backendFetch('/auth/register', {
            method: 'POST',
            body: backendFormData
        })

        const result = await handleResponse(response)

        if (!result.ok) {
            throw new Error(result.error || 'Registration failed')
        }

        showNotification('Registration successful! Please check your email for verification.', 'success')

        setTimeout(() => {
            window.location.href = 'https://login.skreenit.com/login.html'
        }, 2000)

    } catch (error) {
        console.error('Registration error:', error)
        showNotification(error.message || 'Registration failed. Please try again.', 'error')
    } finally {
        submitBtn.textContent = originalText
        submitBtn.disabled = false
    }
}
