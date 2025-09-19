// API Services for Skreenit Dashboard - Supabase Integration
import { supabase, db, auth, storage } from './supabase-config.js'

// Job Services
export const jobService = {
    // Get all jobs with filters
    async getJobs(filters = {}) {
        let query = supabase
            .from('jobs')
            .select(`
                *,
                companies (name, logo_url),
                job_applications (count),
                interview_questions (count)
            `)
        
        if (filters.status) query = query.eq('status', filters.status)
        if (filters.department) query = query.eq('department', filters.department)
        if (filters.created_by) query = query.eq('created_by', filters.created_by)
        if (filters.search) {
            query = query.or(`title.ilike.%${filters.search}%,description.ilike.%${filters.search}%`)
        }
        
        const { data, error } = await query.order('created_at', { ascending: false })
        return { data, error }
    },

    // Get single job with full details
    async getJobById(id) {
        const { data, error } = await supabase
            .from('jobs')
            .select(`
                *,
                companies (*),
                job_skills (*),
                interview_questions (*),
                job_applications (
                    id,
                    status,
                    ai_score,
                    applied_at,
                    users (full_name, email, avatar_url)
                )
            `)
            .eq('id', id)
            .single()
        
        return { data, error }
    },

    // Create new job
    async createJob(jobData) {
        const user = await auth.getCurrentUser()
        if (!user) return { error: 'Not authenticated' }

        const { questions, skills, ...job } = jobData
        job.created_by = user.id

        // Create job
        const { data: jobResult, error: jobError } = await db.insert('jobs', job)
        if (jobError) return { error: jobError }

        const jobId = jobResult[0].id

        // Add skills if provided
        if (skills && skills.length > 0) {
            const skillsData = skills.map(skill => ({
                job_id: jobId,
                skill_name: skill.name,
                is_required: skill.required || false,
                proficiency_level: skill.level || 'intermediate'
            }))
            await db.insert('job_skills', skillsData)
        }

        // Add interview questions if provided
        if (questions && questions.length > 0) {
            const questionsData = questions.map((question, index) => ({
                job_id: jobId,
                question_text: question,
                question_order: index + 1,
                time_limit: 120
            }))
            await db.insert('interview_questions', questionsData)
        }

        return { data: jobResult[0], error: null }
    },

    // Update job
    async updateJob(id, updates) {
        const { data, error } = await db.update('jobs', id, updates)
        return { data, error }
    },

    // Delete job
    async deleteJob(id) {
        const { error } = await db.delete('jobs', id)
        return { error }
    }
}

// Application Services
export const applicationService = {
    // Get applications for a job (recruiter view)
    async getApplicationsByJob(jobId, filters = {}) {
        let query = supabase
            .from('job_applications')
            .select(`
                *,
                users (
                    full_name,
                    email,
                    avatar_url,
                    candidate_profiles (*)
                ),
                video_responses (
                    id,
                    status,
                    ai_analysis,
                    recorded_at
                )
            `)
            .eq('job_id', jobId)

        if (filters.status) query = query.eq('status', filters.status)
        if (filters.min_score) query = query.gte('ai_score', filters.min_score)
        
        const { data, error } = await query.order('applied_at', { ascending: false })
        return { data, error }
    },

    // Get applications for a candidate
    async getCandidateApplications(candidateId) {
        const { data, error } = await supabase
            .from('job_applications')
            .select(`
                *,
                jobs (
                    title,
                    companies (name, logo_url),
                    location,
                    job_type
                ),
                video_responses (count)
            `)
            .eq('candidate_id', candidateId)
            .order('applied_at', { ascending: false })
        
        return { data, error }
    },

    // Submit job application
    async submitApplication(applicationData) {
        const user = await auth.getCurrentUser()
        if (!user) return { error: 'Not authenticated' }

        applicationData.candidate_id = user.id
        
        // Calculate AI score (simplified - in real app, this would be more complex)
        applicationData.ai_score = Math.floor(Math.random() * 30) + 70 // 70-100 range
        
        const { data, error } = await db.insert('job_applications', applicationData)
        return { data, error }
    },

    // Update application status
    async updateApplicationStatus(id, status, notes = '') {
        const updates = { 
            status,
            recruiter_notes: notes,
            updated_at: new Date().toISOString()
        }
        
        const { data, error } = await db.update('job_applications', id, updates)
        return { data, error }
    },

    // Get application analytics
    async getApplicationAnalytics(recruiterId) {
        const { data, error } = await supabase
            .from('job_applications')
            .select(`
                status,
                ai_score,
                applied_at,
                jobs!inner (created_by)
            `)
            .eq('jobs.created_by', recruiterId)
        
        if (error) return { error }

        // Process analytics
        const analytics = {
            total: data.length,
            byStatus: {},
            averageScore: 0,
            recentApplications: 0
        }

        const now = new Date()
        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)

        data.forEach(app => {
            // Count by status
            analytics.byStatus[app.status] = (analytics.byStatus[app.status] || 0) + 1
            
            // Recent applications
            if (new Date(app.applied_at) > weekAgo) {
                analytics.recentApplications++
            }
        })

        // Calculate average score
        const scores = data.filter(app => app.ai_score).map(app => app.ai_score)
        analytics.averageScore = scores.length > 0 
            ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
            : 0

        return { data: analytics, error: null }
    }
}

// Video Interview Services
export const videoService = {
    // Get interview questions for a job
    async getInterviewQuestions(jobId) {
        const { data, error } = await supabase
            .from('interview_questions')
            .select('*')
            .eq('job_id', jobId)
            .order('question_order')
        
        return { data, error }
    },

    // Save video response
    async saveVideoResponse(responseData) {
        const { data, error } = await db.insert('video_responses', responseData)
        return { data, error }
    },

    // Upload video file
    async uploadVideo(applicationId, questionId, videoBlob) {
        const user = await auth.getCurrentUser()
        if (!user) return { error: 'Not authenticated' }

        const fileName = `${user.id}/${applicationId}/${questionId}.webm`
        
        const { data, error } = await storage.uploadFile('videos', fileName, videoBlob)
        if (error) return { error }

        const videoUrl = storage.getPublicUrl('videos', fileName)
        
        // Save video response record
        const responseData = {
            application_id: applicationId,
            question_id: questionId,
            video_url: videoUrl,
            status: 'completed',
            recorded_at: new Date().toISOString()
        }

        return await this.saveVideoResponse(responseData)
    },

    // Get video responses for application
    async getVideoResponses(applicationId) {
        const { data, error } = await supabase
            .from('video_responses')
            .select(`
                *,
                interview_questions (question_text, question_order)
            `)
            .eq('application_id', applicationId)
            .order('interview_questions(question_order)')
        
        return { data, error }
    }
}

// Candidate Services
export const candidateService = {
    // Get candidate profile
    async getProfile(userId) {
        const { data, error } = await supabase
            .from('candidate_profiles')
            .select(`
                *,
                candidate_skills (*),
                candidate_experience (*),
                candidate_education (*)
            `)
            .eq('user_id', userId)
            .single()
        
        return { data, error }
    },

    // Update candidate profile
    async updateProfile(userId, profileData) {
        const { skills, experience, education, ...profile } = profileData
        
        // Update main profile
        const { data, error } = await supabase
            .from('candidate_profiles')
            .upsert({ user_id: userId, ...profile })
            .select()
            .single()
        
        if (error) return { error }

        const profileId = data.id

        // Update skills if provided
        if (skills) {
            await supabase.from('candidate_skills').delete().eq('candidate_id', profileId)
            if (skills.length > 0) {
                const skillsData = skills.map(skill => ({
                    candidate_id: profileId,
                    skill_name: skill.name,
                    proficiency_level: skill.level,
                    years_experience: skill.years || 0
                }))
                await db.insert('candidate_skills', skillsData)
            }
        }

        // Update experience if provided
        if (experience) {
            await supabase.from('candidate_experience').delete().eq('candidate_id', profileId)
            if (experience.length > 0) {
                const expData = experience.map(exp => ({
                    candidate_id: profileId,
                    ...exp
                }))
                await db.insert('candidate_experience', expData)
            }
        }

        return { data, error: null }
    },

    // Search candidates (for recruiters)
    async searchCandidates(filters = {}) {
        let query = supabase
            .from('candidate_profiles')
            .select(`
                *,
                users (full_name, email, avatar_url, location),
                candidate_skills (skill_name, proficiency_level),
                candidate_experience (company_name, position)
            `)

        if (filters.skills) {
            query = query.in('candidate_skills.skill_name', filters.skills)
        }
        if (filters.experience_min) {
            query = query.gte('experience_years', filters.experience_min)
        }
        if (filters.location) {
            query = query.ilike('users.location', `%${filters.location}%`)
        }
        
        const { data, error } = await query.limit(50)
        return { data, error }
    }
}

// Notification Services
export const notificationService = {
    // Get user notifications
    async getNotifications(userId, limit = 20) {
        const { data, error } = await supabase
            .from('notifications')
            .select('*')
            .eq('user_id', userId)
            .order('created_at', { ascending: false })
            .limit(limit)
        
        return { data, error }
    },

    // Create notification
    async createNotification(notificationData) {
        const { data, error } = await db.insert('notifications', notificationData)
        return { data, error }
    },

    // Mark notification as read
    async markAsRead(id) {
        const { data, error } = await db.update('notifications', id, { is_read: true })
        return { data, error }
    },

    // Mark all notifications as read for user
    async markAllAsRead(userId) {
        const { error } = await supabase
            .from('notifications')
            .update({ is_read: true })
            .eq('user_id', userId)
            .eq('is_read', false)
        
        return { error }
    }
}

// Real-time subscriptions
export const realtimeService = {
    // Subscribe to job applications for recruiter
    subscribeToApplications(recruiterId, callback) {
        return db.subscribe('job_applications', (payload) => {
            // Filter for recruiter's jobs only
            if (payload.new && payload.new.job_id) {
                jobService.getJobById(payload.new.job_id).then(({ data: job }) => {
                    if (job && job.created_by === recruiterId) {
                        callback(payload)
                    }
                })
            }
        })
    },

    // Subscribe to application updates for candidate
    subscribeToApplicationUpdates(candidateId, callback) {
        return db.subscribe('job_applications', callback, {
            filter: `candidate_id=eq.${candidateId}`
        })
    },

    // Subscribe to notifications
    subscribeToNotifications(userId, callback) {
        return db.subscribe('notifications', callback, {
            filter: `user_id=eq.${userId}`
        })
    }
}

// Analytics Services
export const analyticsService = {
    // Track event
    async trackEvent(eventType, eventData = {}) {
        const user = await auth.getCurrentUser()
        
        const event = {
            user_id: user?.id || null,
            event_type: eventType,
            event_data: eventData,
            created_at: new Date().toISOString()
        }
        
        const { error } = await db.insert('analytics_events', event)
        return { error }
    },

    // Get recruiter analytics
    async getRecruiterAnalytics(recruiterId, days = 30) {
        const startDate = new Date()
        startDate.setDate(startDate.getDate() - days)

        const { data, error } = await supabase
            .from('analytics_events')
            .select('*')
            .eq('user_id', recruiterId)
            .gte('created_at', startDate.toISOString())
        
        if (error) return { error }

        // Process analytics data
        const analytics = {
            totalEvents: data.length,
            eventsByType: {},
            dailyActivity: {}
        }

        data.forEach(event => {
            // Count by type
            analytics.eventsByType[event.event_type] = 
                (analytics.eventsByType[event.event_type] || 0) + 1
            
            // Count by day
            const day = event.created_at.split('T')[0]
            analytics.dailyActivity[day] = (analytics.dailyActivity[day] || 0) + 1
        })

        return { data: analytics, error: null }
    }
}
