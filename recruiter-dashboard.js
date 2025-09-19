// Recruiter Dashboard JavaScript - Supabase Integration
import { auth, jobService, applicationService, notificationService, realtimeService, analyticsService } from './api-services.js';

class RecruiterDashboard {
    constructor() {
        this.currentSection = 'overview';
        this.currentUser = null;
        this.jobs = [];
        this.candidates = [];
        this.notifications = [];
        this.realtimeSubscriptions = [];
        
        this.init();
    }

    async init() {
        // Check authentication
        await this.checkAuth();
        
        if (this.currentUser) {
            // Load initial data
            await this.loadDashboardData();
            
            // Setup real-time subscriptions
            this.setupRealtimeSubscriptions();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Show overview by default
            this.showSection('overview');
        } else {
            this.redirectToLogin();
        }
    }

    async checkAuth() {
        try {
            this.currentUser = await auth.getCurrentUser();
            if (this.currentUser) {
                // Update UI with user info
                document.querySelector('.user-name').textContent = this.currentUser.full_name || this.currentUser.email;
                if (this.currentUser.avatar_url) {
                    document.querySelector('.user-avatar').src = this.currentUser.avatar_url;
                }
            }
        } catch (error) {
            console.error('Auth check failed:', error);
        }
    }

    async loadDashboardData() {
        try {
            // Load jobs
            const { data: jobs, error: jobsError } = await jobService.getJobs({ 
                created_by: this.currentUser.id 
            });
            if (!jobsError) {
                this.jobs = jobs || [];
            }

            // Load applications for all jobs
            await this.loadApplications();

            // Load notifications
            const { data: notifications, error: notifError } = await notificationService.getNotifications(
                this.currentUser.id
            );
            if (!notifError) {
                this.notifications = notifications || [];
            }

            // Update dashboard counts
            this.updateDashboardCounts();
            
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    async loadApplications() {
        this.candidates = [];
        
        for (const job of this.jobs) {
            const { data: applications, error } = await applicationService.getApplicationsByJob(job.id);
            if (!error && applications) {
                // Transform applications to candidate format
                const jobCandidates = applications.map(app => ({
                    id: app.id,
                    name: app.users?.full_name || 'Unknown',
                    email: app.users?.email || '',
                    job: job.title,
                    jobId: job.id,
                    score: app.ai_score || 0,
                    status: this.formatApplicationStatus(app.status),
                    applied: new Date(app.applied_at).toLocaleDateString(),
                    experience: app.users?.candidate_profiles?.experience_years ? 
                        `${app.users.candidate_profiles.experience_years} years` : 'Not specified',
                    location: app.users?.location || 'Not specified',
                    videoStatus: app.video_responses?.length > 0 ? 'Completed' : 'Pending',
                    applicationData: app
                }));
                
                this.candidates.push(...jobCandidates);
            }
        }
    }

    formatApplicationStatus(status) {
        const statusMap = {
            'applied': 'Applied',
            'screening': 'Under Review',
            'interview_scheduled': 'Interview Scheduled',
            'interviewed': 'Interviewed',
            'offered': 'Offered',
            'hired': 'Hired',
            'rejected': 'Rejected'
        };
        return statusMap[status] || status;
    }

    setupRealtimeSubscriptions() {
        // Subscribe to new applications
        const appSubscription = realtimeService.subscribeToApplications(
            this.currentUser.id,
            (payload) => {
                this.handleNewApplication(payload);
            }
        );
        this.realtimeSubscriptions.push(appSubscription);

        // Subscribe to notifications
        const notifSubscription = realtimeService.subscribeToNotifications(
            this.currentUser.id,
            (payload) => {
                this.handleNewNotification(payload);
            }
        );
        this.realtimeSubscriptions.push(notifSubscription);
    }

    handleNewApplication(payload) {
        if (payload.eventType === 'INSERT') {
            // Reload applications to get the new one
            this.loadApplications().then(() => {
                this.renderCandidates();
                this.updateDashboardCounts();
                this.showNotification('New application received!', 'success');
            });
        }
    }

    handleNewNotification(payload) {
        if (payload.eventType === 'INSERT') {
            this.notifications.unshift(payload.new);
            this.renderNotifications();
        }
    }

    updateDashboardCounts() {
        // Update overview stats
        document.querySelector('.stat-card:nth-child(1) .stat-number').textContent = this.jobs.length;
        document.querySelector('.stat-card:nth-child(2) .stat-number').textContent = this.candidates.length;
        
        const activeJobs = this.jobs.filter(job => job.status === 'published').length;
        document.querySelector('.stat-card:nth-child(3) .stat-number').textContent = activeJobs;
        
        const pendingReviews = this.candidates.filter(c => c.status === 'Applied').length;
        document.querySelector('.stat-card:nth-child(4) .stat-number').textContent = pendingReviews;
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.getAttribute('data-section');
                this.showSection(section);
            });
        });

        // Job creation
        document.getElementById('createJobBtn')?.addEventListener('click', () => {
            this.showCreateJobModal();
        });

        // Job form submission
        document.getElementById('jobForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleJobSubmission(e);
        });

        // Search and filters
        document.getElementById('jobSearch')?.addEventListener('input', (e) => {
            this.filterJobs(e.target.value);
        });

        document.getElementById('candidateSearch')?.addEventListener('input', (e) => {
            this.filterCandidates(e.target.value);
        });

        // Logout
        document.getElementById('logoutBtn')?.addEventListener('click', () => {
            this.handleLogout();
        });
    }

    showSection(section) {
        // Hide all sections
        document.querySelectorAll('.dashboard-section').forEach(s => {
            s.style.display = 'none';
        });

        // Show selected section
        document.getElementById(`${section}Section`).style.display = 'block';

        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-section="${section}"]`).classList.add('active');

        this.currentSection = section;

        // Render section content
        switch (section) {
            case 'overview':
                this.renderOverview();
                break;
            case 'jobs':
                this.renderJobs();
                break;
            case 'candidates':
                this.renderCandidates();
                break;
            case 'analytics':
                this.renderAnalytics();
                break;
        }

        // Track navigation
        analyticsService.trackEvent('page_view', { section });
    }

    renderOverview() {
        this.renderRecentJobs();
        this.renderRecentCandidates();
        this.renderNotifications();
    }

    renderRecentJobs() {
        const container = document.getElementById('recentJobs');
        if (!container) return;

        const recentJobs = this.jobs.slice(0, 5);
        
        container.innerHTML = recentJobs.map(job => `
            <div class="job-item">
                <div class="job-info">
                    <h4>${job.title}</h4>
                    <p>${job.location} • ${job.job_type}</p>
                </div>
                <div class="job-stats">
                    <span class="applications-count">${job.job_applications?.length || 0} applications</span>
                    <span class="job-status status-${job.status.toLowerCase()}">${job.status}</span>
                </div>
            </div>
        `).join('');
    }

    renderRecentCandidates() {
        const container = document.getElementById('recentCandidates');
        if (!container) return;

        const recentCandidates = this.candidates.slice(0, 5);
        
        container.innerHTML = recentCandidates.map(candidate => `
            <div class="candidate-item" onclick="dashboard.showCandidateDetails(${candidate.id})">
                <div class="candidate-info">
                    <h4>${candidate.name}</h4>
                    <p>${candidate.job}</p>
                </div>
                <div class="candidate-stats">
                    <span class="ai-score">Score: ${candidate.score}</span>
                    <span class="candidate-status">${candidate.status}</span>
                </div>
            </div>
        `).join('');
    }

    renderNotifications() {
        const container = document.getElementById('notifications');
        if (!container) return;

        container.innerHTML = this.notifications.slice(0, 10).map(notification => `
            <div class="notification-item ${notification.is_read ? '' : 'unread'}">
                <div class="notification-content">
                    <p>${notification.message}</p>
                    <span class="notification-time">${this.formatTimeAgo(notification.created_at)}</span>
                </div>
            </div>
        `).join('');
    }

    renderJobs() {
        const container = document.getElementById('jobsList');
        if (!container) return;

        container.innerHTML = this.jobs.map(job => `
            <div class="job-card">
                <div class="job-header">
                    <h3>${job.title}</h3>
                    <span class="job-status status-${job.status.toLowerCase()}">${job.status}</span>
                </div>
                <div class="job-details">
                    <p><strong>Department:</strong> ${job.department || 'Not specified'}</p>
                    <p><strong>Location:</strong> ${job.location}</p>
                    <p><strong>Type:</strong> ${job.job_type}</p>
                    <p><strong>Applications:</strong> ${job.job_applications?.length || 0}</p>
                </div>
                <div class="job-actions">
                    <button onclick="dashboard.editJob(${job.id})" class="btn btn-secondary">Edit</button>
                    <button onclick="dashboard.viewApplications(${job.id})" class="btn btn-primary">View Applications</button>
                </div>
            </div>
        `).join('');
    }

    renderCandidates() {
        const container = document.getElementById('candidatesList');
        if (!container) return;

        container.innerHTML = this.candidates.map(candidate => `
            <div class="candidate-card" onclick="dashboard.showCandidateDetails(${candidate.id})">
                <div class="candidate-header">
                    <h3>${candidate.name}</h3>
                    <span class="ai-score-badge">AI Score: ${candidate.score}</span>
                </div>
                <div class="candidate-details">
                    <p><strong>Job:</strong> ${candidate.job}</p>
                    <p><strong>Experience:</strong> ${candidate.experience}</p>
                    <p><strong>Location:</strong> ${candidate.location}</p>
                    <p><strong>Applied:</strong> ${candidate.applied}</p>
                </div>
                <div class="candidate-status">
                    <span class="status-badge status-${candidate.status.toLowerCase().replace(' ', '-')}">${candidate.status}</span>
                    <span class="video-status ${candidate.videoStatus.toLowerCase()}">${candidate.videoStatus}</span>
                </div>
            </div>
        `).join('');
    }

    async renderAnalytics() {
        try {
            const { data: analytics, error } = await applicationService.getApplicationAnalytics(this.currentUser.id);
            
            if (error) {
                console.error('Failed to load analytics:', error);
                return;
            }

            // Render analytics charts and stats
            this.renderAnalyticsCharts(analytics);
            
        } catch (error) {
            console.error('Analytics rendering failed:', error);
        }
    }

    renderAnalyticsCharts(analytics) {
        // Update analytics stats
        document.getElementById('totalApplications').textContent = analytics.total;
        document.getElementById('averageScore').textContent = analytics.averageScore;
        document.getElementById('recentApplications').textContent = analytics.recentApplications;

        // Render status distribution
        const statusContainer = document.getElementById('statusDistribution');
        if (statusContainer && analytics.byStatus) {
            statusContainer.innerHTML = Object.entries(analytics.byStatus).map(([status, count]) => `
                <div class="status-stat">
                    <span class="status-label">${this.formatApplicationStatus(status)}</span>
                    <span class="status-count">${count}</span>
                </div>
            `).join('');
        }
    }

    showCreateJobModal() {
        document.getElementById('jobModal').style.display = 'block';
        document.getElementById('jobForm').reset();
    }

    async handleJobSubmission(e) {
        try {
            const formData = new FormData(e.target);
            const jobData = {
                title: formData.get('title'),
                description: formData.get('description'),
                requirements: formData.get('requirements'),
                department: formData.get('department'),
                location: formData.get('location'),
                job_type: formData.get('jobType'),
                experience_level: formData.get('experience'),
                salary_min: parseInt(formData.get('salaryMin')) || null,
                salary_max: parseInt(formData.get('salaryMax')) || null,
                status: 'draft'
            };

            // Get interview questions
            const questions = [];
            document.querySelectorAll('.question-input').forEach(input => {
                if (input.value.trim()) {
                    questions.push(input.value.trim());
                }
            });

            if (questions.length > 0) {
                jobData.questions = questions;
            }

            const { data, error } = await jobService.createJob(jobData);
            
            if (error) {
                this.showError('Failed to create job: ' + error.message);
                return;
            }

            // Success
            this.jobs.unshift(data);
            this.renderJobs();
            this.updateDashboardCounts();
            this.closeModal('jobModal');
            this.showNotification('Job created successfully!', 'success');

            // Track event
            analyticsService.trackEvent('job_created', { job_id: data.id });

        } catch (error) {
            console.error('Job creation failed:', error);
            this.showError('Failed to create job');
        }
    }

    async showCandidateDetails(candidateId) {
        const candidate = this.candidates.find(c => c.id === candidateId);
        if (!candidate) return;

        // Load full candidate details and video responses
        try {
            const { data: videoResponses } = await videoService.getVideoResponses(candidate.applicationData.id);
            
            // Show candidate modal with details
            this.displayCandidateModal(candidate, videoResponses);
            
        } catch (error) {
            console.error('Failed to load candidate details:', error);
        }
    }

    displayCandidateModal(candidate, videoResponses) {
        const modal = document.getElementById('candidateModal');
        const content = modal.querySelector('.candidate-details-content');
        
        content.innerHTML = `
            <h3>${candidate.name}</h3>
            <div class="candidate-info">
                <p><strong>Email:</strong> ${candidate.email}</p>
                <p><strong>Job Applied:</strong> ${candidate.job}</p>
                <p><strong>AI Score:</strong> ${candidate.score}</p>
                <p><strong>Status:</strong> ${candidate.status}</p>
                <p><strong>Applied Date:</strong> ${candidate.applied}</p>
            </div>
            
            ${videoResponses && videoResponses.length > 0 ? `
                <div class="video-responses">
                    <h4>Video Interview Responses</h4>
                    ${videoResponses.map(response => `
                        <div class="video-response">
                            <p><strong>Question:</strong> ${response.interview_questions.question_text}</p>
                            <video controls width="100%">
                                <source src="${response.video_url}" type="video/webm">
                                Your browser does not support video playback.
                            </video>
                        </div>
                    `).join('')}
                </div>
            ` : '<p>No video responses available.</p>'}
            
            <div class="candidate-actions">
                <button onclick="dashboard.updateCandidateStatus(${candidate.id}, 'interview_scheduled')" class="btn btn-primary">Schedule Interview</button>
                <button onclick="dashboard.updateCandidateStatus(${candidate.id}, 'rejected')" class="btn btn-danger">Reject</button>
            </div>
        `;
        
        modal.style.display = 'block';
    }

    async updateCandidateStatus(candidateId, newStatus) {
        try {
            const candidate = this.candidates.find(c => c.id === candidateId);
            if (!candidate) return;

            const { error } = await applicationService.updateApplicationStatus(
                candidate.applicationData.id, 
                newStatus
            );

            if (error) {
                this.showError('Failed to update candidate status');
                return;
            }

            // Update local data
            candidate.status = this.formatApplicationStatus(newStatus);
            candidate.applicationData.status = newStatus;

            // Refresh display
            this.renderCandidates();
            this.closeModal('candidateModal');
            this.showNotification('Candidate status updated successfully!', 'success');

        } catch (error) {
            console.error('Failed to update candidate status:', error);
            this.showError('Failed to update candidate status');
        }
    }

    filterJobs(searchTerm) {
        const filteredJobs = this.jobs.filter(job => 
            job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            job.department.toLowerCase().includes(searchTerm.toLowerCase())
        );
        
        // Re-render with filtered jobs
        const container = document.getElementById('jobsList');
        container.innerHTML = filteredJobs.map(job => `
            <div class="job-card">
                <div class="job-header">
                    <h3>${job.title}</h3>
                    <span class="job-status status-${job.status.toLowerCase()}">${job.status}</span>
                </div>
                <div class="job-details">
                    <p><strong>Department:</strong> ${job.department || 'Not specified'}</p>
                    <p><strong>Location:</strong> ${job.location}</p>
                    <p><strong>Type:</strong> ${job.job_type}</p>
                    <p><strong>Applications:</strong> ${job.job_applications?.length || 0}</p>
                </div>
                <div class="job-actions">
                    <button onclick="dashboard.editJob(${job.id})" class="btn btn-secondary">Edit</button>
                    <button onclick="dashboard.viewApplications(${job.id})" class="btn btn-primary">View Applications</button>
                </div>
            </div>
        `).join('');
    }

    filterCandidates(searchTerm) {
        const filteredCandidates = this.candidates.filter(candidate => 
            candidate.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            candidate.job.toLowerCase().includes(searchTerm.toLowerCase()) ||
            candidate.email.toLowerCase().includes(searchTerm.toLowerCase())
        );
        
        // Re-render with filtered candidates
        const container = document.getElementById('candidatesList');
        container.innerHTML = filteredCandidates.map(candidate => `
            <div class="candidate-card" onclick="dashboard.showCandidateDetails(${candidate.id})">
                <div class="candidate-header">
                    <h3>${candidate.name}</h3>
                    <span class="ai-score-badge">AI Score: ${candidate.score}</span>
                </div>
                <div class="candidate-details">
                    <p><strong>Job:</strong> ${candidate.job}</p>
                    <p><strong>Experience:</strong> ${candidate.experience}</p>
                    <p><strong>Location:</strong> ${candidate.location}</p>
                    <p><strong>Applied:</strong> ${candidate.applied}</p>
                </div>
                <div class="candidate-status">
                    <span class="status-badge status-${candidate.status.toLowerCase().replace(' ', '-')}">${candidate.status}</span>
                    <span class="video-status ${candidate.videoStatus.toLowerCase()}">${candidate.videoStatus}</span>
                </div>
            </div>
        `).join('');
    }

    closeModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    formatTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffInMinutes = Math.floor((now - date) / (1000 * 60));
        
        if (diffInMinutes < 60) {
            return `${diffInMinutes} minutes ago`;
        } else if (diffInMinutes < 1440) {
            return `${Math.floor(diffInMinutes / 60)} hours ago`;
        } else {
            return `${Math.floor(diffInMinutes / 1440)} days ago`;
        }
    }

    redirectToLogin() {
        window.location.href = '/login.html';
    }

    async handleLogout() {
        try {
            // Cleanup subscriptions
            this.realtimeSubscriptions.forEach(subscription => {
                if (subscription && subscription.unsubscribe) {
                    subscription.unsubscribe();
                }
            });

            await auth.signOut();
            this.redirectToLogin();
            
        } catch (error) {
            console.error('Logout failed:', error);
        }
    }

    // Cleanup on page unload
    cleanup() {
        this.realtimeSubscriptions.forEach(subscription => {
            if (subscription && subscription.unsubscribe) {
                subscription.unsubscribe();
            }
        });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new RecruiterDashboard();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.dashboard) {
        window.dashboard.cleanup();
    }
});

// Modal event listeners
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.style.display = 'none';
    }
    
    if (e.target.classList.contains('close')) {
        e.target.closest('.modal').style.display = 'none';
    }
});

// Add question input for job creation
function addQuestionInput() {
    const container = document.getElementById('questionsContainer');
    const questionDiv = document.createElement('div');
    questionDiv.className = 'question-group';
    questionDiv.innerHTML = `
        <input type="text" class="question-input" placeholder="Enter interview question">
        <button type="button" onclick="this.parentElement.remove()" class="btn btn-danger btn-sm">Remove</button>
    `;
    container.appendChild(questionDiv);
}

// Make function globally available
window.addQuestionInput = addQuestionInput;
