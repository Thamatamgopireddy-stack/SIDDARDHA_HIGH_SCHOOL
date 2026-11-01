export interface SuccessEnvelope<T> {
  success: true
  data: T
  message: string
  meta: Record<string, unknown> | null
}

export interface ApiErrorEnvelope {
  success: false
  error: {
    code: string
    message: string
    details: Record<string, unknown>
  }
}

export interface Page<T> {
  items: T[]
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface Profile {
  id: string
  school_id: string
  display_name: string
  email: string | null
  phone: string | null
  is_active: boolean
  must_change_password: boolean
  account_status: string
  email_verified: boolean
  created_at: string
}

export interface AccountStatus {
  account_status: string
  email_verified: boolean
  full_name: string
  email: string
  requested_role: 'admin' | 'staff' | null
  rejection_reason: string | null
  created_at: string | null
  roles: string[]
  permissions: string[]
  portal: 'super_admin' | 'admin' | 'staff' | null
}

export interface RegistrationRequest {
  id: string
  applicant_user_id: string
  full_name: string
  email: string
  phone_number: string
  employee_id: string | null
  department: string
  designation: string
  staff_category: string | null
  requested_role: 'admin' | 'staff'
  email_verified: boolean
  status: 'pending' | 'approved' | 'rejected'
  rejection_reason: string | null
  created_at: string
}

export interface Student {
  id: string
  admission_number: string
  first_name: string
  last_name: string
  date_of_birth: string | null
  class_name: string
  section: string
  roll_number: string
  status: 'active' | 'inactive' | 'graduated' | 'transferred'
  created_at: string
  updated_at: string
}

export interface Teacher {
  id: string
  employee_number: string
  first_name: string
  last_name: string
  email: string | null
  phone: string | null
  status: 'active' | 'inactive' | 'on_leave'
  created_at: string
  updated_at: string
}

export interface Admission {
  id: string
  application_number: string
  applicant_name: string
  requested_class: string
  guardian_name: string
  guardian_phone: string
  status: 'submitted' | 'under_review' | 'approved' | 'rejected' | 'converted'
  created_at: string
  updated_at: string
}

export interface AttendanceRecord {
  id: string
  student_id: string
  attendance_date: string
  session: string
  status: 'present' | 'absent' | 'late' | 'excused'
  remarks: string | null
}
