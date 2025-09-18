# Skreenit Dashboard - Supabase Integration Setup Guide

This guide will help you set up and deploy the Skreenit recruitment dashboard with Supabase backend integration.

## 📋 Prerequisites

- Supabase account (free tier available)
- Modern web browser with ES6 module support
- Text editor or IDE
- Basic understanding of SQL and JavaScript

## 🚀 Step 1: Supabase Project Setup

### 1.1 Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Sign up or log in to your account
3. Click "New Project"
4. Fill in project details:
   - **Name**: Skreenit Dashboard
   - **Database Password**: Choose a strong password
   - **Region**: Select closest to your users
5. Click "Create new project"
6. Wait for project initialization (2-3 minutes)

### 1.2 Get Project Credentials
1. In your Supabase dashboard, go to **Settings > API**
2. Copy the following values:
   - **Project URL** (looks like: `https://your-project-id.supabase.co`)
   - **Anon public key** (starts with `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`)

## 🗄️ Step 2: Database Schema Setup

### 2.1 Run Database Schema
1. In your Supabase dashboard, go to **SQL Editor**
2. Open the `database-schema.sql` file from your project
3. Copy the entire contents and paste into the SQL Editor
4. Click **Run** to execute the schema
5. Verify tables are created in **Table Editor**

### 2.2 Enable Row Level Security
The schema automatically enables RLS policies. Verify in **Authentication > Policies** that policies are active for all tables.

### 2.3 Configure Storage
1. Go to **Storage** in Supabase dashboard
2. Verify these buckets are created:
   - `resumes` (for candidate resume uploads)
   - `videos` (for video interview responses)
   - `avatars` (for user profile pictures)

## ⚙️ Step 3: Configure Application

### 3.1 Update Supabase Configuration
1. Open `supabase-config.js`
2. Replace the placeholder values:
```javascript
const SUPABASE_URL = 'https://your-project-id.supabase.co'
const SUPABASE_ANON_KEY = 'your-anon-key-here'
```

### 3.2 File Structure
Ensure your project has these files:
```
├── supabase-config.js          # Supabase client configuration
├── api-services.js             # API service functions
├── database-schema.sql         # Database schema
├── dashboard-styles.css        # Dashboard styling
├── recruiter-dashboard.html    # Recruiter interface
├── recruiter-dashboard.js      # Recruiter functionality
├── candidate-dashboard.html    # Candidate interface
├── candidate-dashboard.js      # Candidate functionality
└── SUPABASE_SETUP_GUIDE.md    # This guide
```

## 👥 Step 4: User Authentication Setup

### 4.1 Configure Auth Settings
1. In Supabase dashboard, go to **Authentication > Settings**
2. Configure these settings:
   - **Site URL**: Your domain (e.g., `https://yourdomain.com`)
   - **Redirect URLs**: Add your dashboard URLs
   - **Email Templates**: Customize if needed

### 4.2 Enable Auth Providers
1. Go to **Authentication > Providers**
2. Enable desired providers:
   - **Email** (enabled by default)
   - **Google** (optional)
   - **LinkedIn** (optional for professional platform)

### 4.3 Create User Roles
The schema includes user roles. You can manually set roles in the database:
```sql
-- Make a user a recruiter
UPDATE users SET role = 'recruiter' WHERE email = 'recruiter@company.com';

-- Make a user a candidate
UPDATE users SET role = 'candidate' WHERE email = 'candidate@email.com';
```

## 🌐 Step 5: Deployment Options

### Option A: Static Hosting (Netlify/Vercel)
1. Push code to GitHub repository
2. Connect repository to Netlify or Vercel
3. Set build settings:
   - **Build command**: None (static files)
   - **Publish directory**: `/` (root)
4. Add environment variables if needed
5. Deploy

### Option B: Local Development
1. Use a local web server (Python, Node.js, or VS Code Live Server)
2. Serve files over HTTP (not file://) for ES6 modules to work
3. Example with Python:
```bash
python -m http.server 8000
```
4. Access at `http://localhost:8000`

### Option C: GitHub Pages
1. Push to GitHub repository
2. Go to repository **Settings > Pages**
3. Select source branch (usually `main`)
4. Access at `https://username.github.io/repository-name`

## 🧪 Step 6: Testing the Integration

### 6.1 Test User Registration
1. Open candidate dashboard
2. Try registering a new account
3. Check Supabase **Authentication > Users** for new user
4. Verify user appears in `users` table

### 6.2 Test Job Creation (Recruiter)
1. Set a user's role to 'recruiter' in database
2. Login to recruiter dashboard
3. Create a new job posting
4. Verify job appears in `jobs` table
5. Check that interview questions are saved

### 6.3 Test Job Application (Candidate)
1. Login as candidate
2. Browse available jobs
3. Apply to a job
4. Verify application in `job_applications` table
5. Test video interview functionality

### 6.4 Test Real-time Features
1. Open recruiter dashboard in one browser
2. Apply to job in another browser (as candidate)
3. Verify real-time notification appears in recruiter dashboard

## 🔧 Step 7: Customization

### 7.1 Branding
- Update logo and colors in `dashboard-styles.css`
- Modify company name in HTML files
- Customize email templates in Supabase

### 7.2 Additional Features
- Add more job fields in schema and forms
- Implement advanced search filters
- Add email notifications
- Integrate with external job boards

### 7.3 Security Enhancements
- Review and customize RLS policies
- Add rate limiting
- Implement additional validation
- Add audit logging

## 🐛 Troubleshooting

### Common Issues

**1. "Module not found" errors**
- Ensure you're serving files over HTTP, not file://
- Check that all file paths are correct
- Verify ES6 modules are supported in your browser

**2. Supabase connection errors**
- Verify SUPABASE_URL and SUPABASE_ANON_KEY are correct
- Check network connectivity
- Ensure Supabase project is active

**3. Authentication issues**
- Verify auth settings in Supabase dashboard
- Check redirect URLs are configured
- Ensure RLS policies allow user operations

**4. Database permission errors**
- Check RLS policies are properly configured
- Verify user roles are set correctly
- Ensure authenticated users have necessary permissions

**5. Real-time subscriptions not working**
- Verify Supabase project has real-time enabled
- Check browser console for WebSocket errors
- Ensure proper cleanup of subscriptions

### Debug Mode
Add this to your browser console to enable debug logging:
```javascript
localStorage.setItem('supabase.debug', 'true');
```

## 📊 Step 8: Monitoring and Analytics

### 8.1 Supabase Analytics
- Monitor database usage in Supabase dashboard
- Track API requests and performance
- Review authentication metrics

### 8.2 Application Analytics
- The `analytics_events` table tracks user interactions
- Create custom dashboards for recruitment metrics
- Monitor video interview completion rates

## 🔄 Step 9: Maintenance

### Regular Tasks
- Monitor database storage usage
- Review and update RLS policies
- Clean up old video files
- Update dependencies
- Backup important data

### Performance Optimization
- Add database indexes for frequently queried fields
- Optimize large queries
- Implement pagination for large datasets
- Consider CDN for video files

## 📞 Support

For issues with this integration:
1. Check browser console for errors
2. Review Supabase logs in dashboard
3. Verify all setup steps were completed
4. Test with minimal example first

## 🎉 Congratulations!

Your Skreenit recruitment dashboard with Supabase integration is now ready! You have:

✅ Complete database schema with RLS security
✅ Real-time recruiter and candidate dashboards  
✅ Video interview functionality
✅ File upload capabilities
✅ User authentication and authorization
✅ Responsive design for all devices
✅ Analytics and reporting features

The platform is now ready for production use with a scalable, secure backend powered by Supabase.
