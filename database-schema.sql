-- Supabase Database Schema for Skreenit Recruitment Platform
-- Run these SQL commands in your Supabase SQL Editor

-- Enable Row Level Security
ALTER DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;

-- Create custom types
CREATE TYPE user_role AS ENUM ('recruiter', 'candidate', 'admin');
CREATE TYPE job_status AS ENUM ('draft', 'active', 'paused', 'closed');
CREATE TYPE application_status AS ENUM ('submitted', 'under_review', 'video_pending', 'video_completed', 'interview_scheduled', 'rejected', 'hired');
CREATE TYPE video_status AS ENUM ('not_started', 'in_progress', 'completed', 'failed');

-- Users table (extends Supabase auth.users)
CREATE TABLE public.users (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    role user_role NOT NULL DEFAULT 'candidate',
    avatar_url TEXT,
    phone TEXT,
    location TEXT,
    company TEXT, -- for recruiters
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Companies table
CREATE TABLE public.companies (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    website TEXT,
    logo_url TEXT,
    industry TEXT,
    size TEXT,
    location TEXT,
    created_by UUID REFERENCES public.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Jobs table
CREATE TABLE public.jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    requirements TEXT NOT NULL,
    responsibilities TEXT,
    department TEXT,
    location TEXT NOT NULL,
    job_type TEXT NOT NULL, -- full-time, part-time, contract, internship
    experience_level TEXT, -- entry, mid, senior, lead
    salary_min INTEGER,
    salary_max INTEGER,
    currency TEXT DEFAULT 'INR',
    status job_status DEFAULT 'draft',
    company_id UUID REFERENCES public.companies(id),
    created_by UUID REFERENCES public.users(id) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Job Skills table (many-to-many relationship)
CREATE TABLE public.job_skills (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id UUID REFERENCES public.jobs(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    is_required BOOLEAN DEFAULT false,
    proficiency_level TEXT -- beginner, intermediate, advanced, expert
);

-- Video Interview Questions table
CREATE TABLE public.interview_questions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id UUID REFERENCES public.jobs(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_order INTEGER NOT NULL,
    time_limit INTEGER DEFAULT 120, -- seconds
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Candidate Profiles table
CREATE TABLE public.candidate_profiles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE UNIQUE,
    title TEXT, -- job title/position
    bio TEXT,
    experience_years INTEGER,
    current_salary INTEGER,
    expected_salary INTEGER,
    currency TEXT DEFAULT 'INR',
    resume_url TEXT,
    portfolio_url TEXT,
    linkedin_url TEXT,
    github_url TEXT,
    availability TEXT, -- immediate, 2weeks, 1month, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Candidate Skills table
CREATE TABLE public.candidate_skills (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    candidate_id UUID REFERENCES public.candidate_profiles(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    proficiency_level TEXT, -- beginner, intermediate, advanced, expert
    years_experience INTEGER
);

-- Candidate Experience table
CREATE TABLE public.candidate_experience (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    candidate_id UUID REFERENCES public.candidate_profiles(id) ON DELETE CASCADE,
    company_name TEXT NOT NULL,
    position TEXT NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Candidate Education table
CREATE TABLE public.candidate_education (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    candidate_id UUID REFERENCES public.candidate_profiles(id) ON DELETE CASCADE,
    institution TEXT NOT NULL,
    degree TEXT NOT NULL,
    field_of_study TEXT,
    start_date DATE,
    end_date DATE,
    grade TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Job Applications table
CREATE TABLE public.job_applications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id UUID REFERENCES public.jobs(id) ON DELETE CASCADE,
    candidate_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    status application_status DEFAULT 'submitted',
    cover_letter TEXT,
    resume_url TEXT,
    ai_score INTEGER, -- 0-100 AI matching score
    ai_analysis JSONB, -- detailed AI analysis results
    recruiter_notes TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(job_id, candidate_id) -- prevent duplicate applications
);

-- Video Interview Responses table
CREATE TABLE public.video_responses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    application_id UUID REFERENCES public.job_applications(id) ON DELETE CASCADE,
    question_id UUID REFERENCES public.interview_questions(id) ON DELETE CASCADE,
    video_url TEXT,
    transcript TEXT,
    duration INTEGER, -- seconds
    ai_analysis JSONB, -- sentiment, keywords, confidence score, etc.
    status video_status DEFAULT 'not_started',
    recorded_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(application_id, question_id)
);

-- Notifications table
CREATE TABLE public.notifications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT NOT NULL, -- application, interview, message, system
    related_id UUID, -- ID of related job, application, etc.
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Analytics Events table
CREATE TABLE public.analytics_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id),
    event_type TEXT NOT NULL, -- job_view, application_submit, video_complete, etc.
    event_data JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_jobs_status ON public.jobs(status);
CREATE INDEX idx_jobs_created_by ON public.jobs(created_by);
CREATE INDEX idx_jobs_company ON public.jobs(company_id);
CREATE INDEX idx_applications_job ON public.job_applications(job_id);
CREATE INDEX idx_applications_candidate ON public.job_applications(candidate_id);
CREATE INDEX idx_applications_status ON public.job_applications(status);
CREATE INDEX idx_video_responses_application ON public.video_responses(application_id);
CREATE INDEX idx_notifications_user ON public.notifications(user_id, is_read);
CREATE INDEX idx_analytics_user ON public.analytics_events(user_id);
CREATE INDEX idx_analytics_type ON public.analytics_events(event_type);

-- Enable Row Level Security (RLS)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.candidate_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.candidate_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.candidate_experience ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.candidate_education ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.video_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analytics_events ENABLE ROW LEVEL SECURITY;

-- RLS Policies

-- Users can view and update their own profile
CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (auth.uid() = id);

-- Companies can be viewed by all, managed by creators
CREATE POLICY "Companies are viewable by all" ON public.companies
    FOR SELECT USING (true);

CREATE POLICY "Users can create companies" ON public.companies
    FOR INSERT WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Company creators can update" ON public.companies
    FOR UPDATE USING (auth.uid() = created_by);

-- Jobs policies
CREATE POLICY "Jobs are viewable by all" ON public.jobs
    FOR SELECT USING (status = 'active' OR auth.uid() = created_by);

CREATE POLICY "Recruiters can create jobs" ON public.jobs
    FOR INSERT WITH CHECK (
        auth.uid() = created_by AND 
        EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'recruiter')
    );

CREATE POLICY "Job creators can update" ON public.jobs
    FOR UPDATE USING (auth.uid() = created_by);

-- Job applications policies
CREATE POLICY "Candidates can view own applications" ON public.job_applications
    FOR SELECT USING (
        auth.uid() = candidate_id OR 
        auth.uid() IN (SELECT created_by FROM public.jobs WHERE id = job_id)
    );

CREATE POLICY "Candidates can create applications" ON public.job_applications
    FOR INSERT WITH CHECK (auth.uid() = candidate_id);

CREATE POLICY "Recruiters can update applications" ON public.job_applications
    FOR UPDATE USING (
        auth.uid() IN (SELECT created_by FROM public.jobs WHERE id = job_id)
    );

-- Video responses policies
CREATE POLICY "Video responses viewable by candidate and recruiter" ON public.video_responses
    FOR SELECT USING (
        auth.uid() IN (
            SELECT candidate_id FROM public.job_applications WHERE id = application_id
            UNION
            SELECT j.created_by FROM public.jobs j 
            JOIN public.job_applications ja ON j.id = ja.job_id 
            WHERE ja.id = application_id
        )
    );

CREATE POLICY "Candidates can create video responses" ON public.video_responses
    FOR INSERT WITH CHECK (
        auth.uid() IN (
            SELECT candidate_id FROM public.job_applications WHERE id = application_id
        )
    );

-- Notifications policies
CREATE POLICY "Users can view own notifications" ON public.notifications
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own notifications" ON public.notifications
    FOR UPDATE USING (auth.uid() = user_id);

-- Functions and triggers

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON public.companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON public.jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_candidate_profiles_updated_at BEFORE UPDATE ON public.candidate_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_job_applications_updated_at BEFORE UPDATE ON public.job_applications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to create user profile after signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, full_name)
    VALUES (NEW.id, NEW.email, NEW.raw_user_meta_data->>'full_name');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create user profile
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Create storage buckets
INSERT INTO storage.buckets (id, name, public) VALUES 
    ('resumes', 'resumes', false),
    ('videos', 'videos', false),
    ('avatars', 'avatars', true),
    ('company-logos', 'company-logos', true);

-- Storage policies
CREATE POLICY "Users can upload own resume" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'resumes' AND 
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can view own resume" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'resumes' AND 
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can upload own videos" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'videos' AND 
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Recruiters can view candidate videos" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'videos' AND (
            auth.uid()::text = (storage.foldername(name))[1] OR
            EXISTS (
                SELECT 1 FROM public.users 
                WHERE id = auth.uid() AND role = 'recruiter'
            )
        )
    );

CREATE POLICY "Anyone can view avatars" ON storage.objects
    FOR SELECT USING (bucket_id = 'avatars');

CREATE POLICY "Users can upload own avatar" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'avatars' AND 
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Anyone can view company logos" ON storage.objects
    FOR SELECT USING (bucket_id = 'company-logos');
