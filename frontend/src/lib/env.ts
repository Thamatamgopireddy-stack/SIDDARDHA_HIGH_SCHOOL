const env = import.meta.env

export const appConfig = {
  apiBaseUrl: env.VITE_API_BASE_URL?.trim().replace(/\/+$/, '') ?? '',
  supabaseUrl: env.VITE_SUPABASE_URL?.trim() ?? '',
  supabaseAnonKey: env.VITE_SUPABASE_ANON_KEY?.trim() ?? '',
  appName: env.VITE_APP_NAME?.trim() || 'EduCore ERP',
  schoolName: env.VITE_APP_SCHOOL_NAME?.trim() || 'SIDDARDHA HIGH SCHOOL',
  environment: env.VITE_APP_ENV?.trim() || 'development',
}

export const supabaseConfigured = Boolean(appConfig.supabaseUrl && appConfig.supabaseAnonKey)
export const apiConfigured = Boolean(appConfig.apiBaseUrl)
