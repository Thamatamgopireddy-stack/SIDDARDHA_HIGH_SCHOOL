import { createClient } from '@supabase/supabase-js'
import { appConfig, supabaseConfigured } from './env'

export const supabase = supabaseConfigured
  ? createClient(appConfig.supabaseUrl, appConfig.supabaseAnonKey, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
      },
    })
  : null
