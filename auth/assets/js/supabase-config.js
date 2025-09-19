// Supabase Configuration and Client Setup
import { createClient } from 'https://cdn.skypack.dev/@supabase/supabase-js@2'

const SUPABASE_URL = 'https://kokxhrjmlwhtkssqsjuf.supabase.co'
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imtva3hocmptbHdodGtzc3FzanVmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUxNjMxNTUsImV4cCI6MjA3MDczOTE1NX0.mB-L3Y9YKFTCiMDtKrsveo_b2mJ0s4RGEoom854TbHA'

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

export const auth = {
  async signUp(email, password, userData = {}) {
    const { data, error } = await supabase.auth.signUp({ email, password, options: { data: userData } })
    return { data, error }
  },
  async signIn(email, password) {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    return { data, error }
  },
  async signOut() { const { error } = await supabase.auth.signOut(); return { error } },
  async getCurrentUser() { const { data: { user } } = await supabase.auth.getUser(); return user },
  onAuthStateChange(callback) { return supabase.auth.onAuthStateChange(callback) }
}

export const db = {
  async insert(table, data) { const { data: res, error } = await supabase.from(table).insert(data).select(); return { data: res, error } }
}

export const storage = {
  async uploadFile(bucket, path, file) { const { data, error } = await supabase.storage.from(bucket).upload(path, file); return { data, error } },
  getPublicUrl(bucket, path) { const { data } = supabase.storage.from(bucket).getPublicUrl(path); return data.publicUrl }
}
