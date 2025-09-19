-- Supabase setup for Skreenit Applicants flow
-- Run this in the Supabase SQL editor for your project

-- Extensions
create extension if not exists pgcrypto;

-- 1) Drafts table
create table if not exists public.candidate_form_drafts (
  user_id uuid primary key references auth.users(id) on delete cascade,
  data jsonb not null default '{}',
  status text not null default 'draft',
  updated_at timestamptz not null default now()
);

alter table public.candidate_form_drafts enable row level security;

-- Owner can select their own draft
create policy if not exists "drafts_select_owner"
  on public.candidate_form_drafts
  for select
  to authenticated
  using (auth.uid() = user_id);

-- Owner can upsert/update their own draft
create policy if not exists "drafts_upsert_owner"
  on public.candidate_form_drafts
  for insert
  to authenticated
  with check (auth.uid() = user_id);

create policy if not exists "drafts_update_owner"
  on public.candidate_form_drafts
  for update
  to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- 2) Applications table
create table if not exists public.candidate_applications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  data jsonb not null default '{}',
  status text not null default 'submitted',
  submitted_at timestamptz not null default now()
);

alter table public.candidate_applications enable row level security;

-- Owner can read their applications
create policy if not exists "apps_select_owner"
  on public.candidate_applications
  for select
  to authenticated
  using (auth.uid() = user_id);

-- Owner can insert a new application
create policy if not exists "apps_insert_owner"
  on public.candidate_applications
  for insert
  to authenticated
  with check (auth.uid() = user_id);

-- 3) Storage bucket for application documents
insert into storage.buckets (id, name, public)
values ('applications', 'applications', true)
on conflict (id) do nothing;

-- Storage policies for the 'applications' bucket
-- Allow public read (optional). Remove if you prefer signed URLs only.
create policy if not exists "objects_read_public"
  on storage.objects
  for select
  to public
  using (bucket_id = 'applications');

-- Authenticated users can upload files into a folder that matches their user id
-- Enforces that the first path segment equals the user's UID
create policy if not exists "objects_insert_owner_folder"
  on storage.objects
  for insert
  to authenticated
  with check (
    bucket_id = 'applications'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

-- Owner can update/delete their own files in their folder
create policy if not exists "objects_update_owner"
  on storage.objects
  for update
  to authenticated
  using (
    bucket_id = 'applications'
    and (storage.foldername(name))[1] = auth.uid()::text
  )
  with check (
    bucket_id = 'applications'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy if not exists "objects_delete_owner"
  on storage.objects
  for delete
  to authenticated
  using (
    bucket_id = 'applications'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

-- Optional: Index to speed up filtering by user_id
create index if not exists idx_candidate_applications_user on public.candidate_applications (user_id);
