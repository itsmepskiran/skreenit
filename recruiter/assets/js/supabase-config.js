// Supabase Configuration and Client Setup
import { createClient } from 'https://cdn.skypack.dev/@supabase/supabase-js@2'

const SUPABASE_URL = 'https://kokxhrjmlwhtkssqsjuf.supabase.co'
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imtva3hocmptbHdodGtzc3FzanVmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUxNjMxNTUsImV4cCI6MjA3MDczOTE1NX0.mB-L3Y9YKFTCiMDtKrsveo_b2mJ0s4RGEoom854TbHA'

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
