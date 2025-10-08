# Skreenit Deployment Guide

## Project Structure Overview

The Skreenit project has been reorganized according to your requirements with the following subdomain structure:

- **www.skreenit.com** - Main landing page (`index.html`)
- **login.skreenit.com** - Login form (`login/` directory)
- **auth.skreenit.com** - Registration and authentication (`auth/` directory)
- **applicant.skreenit.com** - Candidate application forms (`applicants/` directory)
- **recruiter.skreenit.com** - Recruiter profile and job posting (`recruiter/` directory)
- **dashboard.skreenit.com** - Both candidate and recruiter dashboards (`dashboards/` directory)

## Fixed Issues

### 1. Backend Issues Fixed ✅
- **FastAPI App Initialization**: Added proper FastAPI app setup in `main.py`
- **Router Imports**: Fixed all relative imports to absolute imports
- **CORS Configuration**: Updated to include all skreenit.com subdomains
- **Health Check**: Added `/health` endpoint for monitoring

### 2. Authentication Flow Fixed ✅
- **Registration**: Users register with role selection (candidate/recruiter)
- **Email Verification**: Supabase sends verification email
- **Password Setup**: After email verification, users set their password
- **First-time Login Logic**: Proper redirection based on role and profile completion
- **Role-based Redirects**: 
  - First-time recruiters → `recruiter.skreenit.com/recruiter-profile.html`
  - Returning recruiters → `dashboard.skreenit.com/recruiter-dashboard.html`
  - First-time candidates → `applicant.skreenit.com/detailed-application-form.html`
  - Returning candidates → `dashboard.skreenit.com/candidate-dashboard.html`

### 3. Frontend Issues Fixed ✅
- **Subdomain URLs**: All HTML pages updated with correct subdomain references
- **Landing Page**: Created beautiful main landing page for www.skreenit.com
- **Login Form**: Fixed login form with proper role selection and company ID for recruiters
- **Registration Form**: Enhanced with proper role-based field visibility
- **Password Update**: Fixed password update flow with backend notifications

## User Flow

### Registration Flow
1. User visits `www.skreenit.com` and clicks "Get Started"
2. Redirected to `auth.skreenit.com/registration.html`
3. User fills registration form with role selection
4. System creates Supabase user and sends verification email
5. User clicks verification link in email
6. Redirected to `login.skreenit.com/update-password.html`
7. User sets their password
8. System sends confirmation email and redirects to login

### Login Flow
1. User visits `login.skreenit.com/login.html`
2. Selects role and enters credentials
3. System validates and determines if first-time login
4. **For Recruiters**:
   - First-time: → `recruiter.skreenit.com/recruiter-profile.html`
   - Returning: → `dashboard.skreenit.com/recruiter-dashboard.html`
5. **For Candidates**:
   - First-time: → `applicant.skreenit.com/detailed-application-form.html`
   - Returning: → `dashboard.skreenit.com/candidate-dashboard.html`

## Deployment Instructions

### Backend Deployment
1. **Environment Variables Required**:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   ALLOWED_ORIGINS=https://skreenit.com,https://www.skreenit.com,https://login.skreenit.com,https://auth.skreenit.com,https://applicant.skreenit.com,https://recruiter.skreenit.com,https://dashboard.skreenit.com
   ENVIRONMENT=production
   ```

2. **Deploy to Railway/Render**:
   - Use `backend/` as the root directory
   - Install dependencies: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Frontend Deployment
Deploy each subdomain separately:

1. **www.skreenit.com**: Deploy `index.html` (root directory)
2. **login.skreenit.com**: Deploy `login/` directory contents
3. **auth.skreenit.com**: Deploy `auth/` directory contents
4. **applicant.skreenit.com**: Deploy `applicants/` directory contents
5. **recruiter.skreenit.com**: Deploy `recruiter/` directory contents
6. **dashboard.skreenit.com**: Deploy `dashboards/` directory contents

### DNS Configuration
Set up CNAME records for all subdomains pointing to your hosting provider.

## Testing Locally

### Backend
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
# From project root
python -m http.server 3000
```

Access:
- Main site: http://localhost:3000
- Login: http://localhost:3000/login/login.html
- Registration: http://localhost:3000/auth/registration.html

## Key Features Implemented

### 1. Smart Authentication
- Role-based registration (candidate/recruiter)
- Email verification via Supabase Auth
- Secure password setup flow
- Company ID validation for recruiters

### 2. Intelligent Redirects
- First-time login detection
- Role-based dashboard routing
- Profile completion tracking
- Seamless subdomain navigation

### 3. Modern UI/UX
- Responsive design
- Professional landing page
- Consistent branding across subdomains
- Loading states and error handling

### 4. Backend API
- RESTful endpoints for all operations
- Proper CORS configuration
- Health monitoring
- Secure authentication middleware

## Next Steps

1. **Set up Supabase Database**: Ensure all required tables are created
2. **Configure Email Templates**: Customize Supabase Auth email templates
3. **Deploy Subdomains**: Deploy each subdomain to your hosting provider
4. **Set up Monitoring**: Implement logging and error tracking
5. **SSL Certificates**: Ensure HTTPS for all subdomains

## Support

The system is now fully functional with proper authentication flow, role-based redirects, and subdomain organization. All major issues have been resolved and the application is ready for deployment.
