import { createContext } from 'react'
import type { Session } from '@supabase/supabase-js'
import type { AccountStatus } from '../../lib/types'

export interface AuthContextValue {
  session: Session | null
  loading: boolean
  configured: boolean
  accountStatus: AccountStatus | null
  statusError: string
  refreshAccountStatus: () => Promise<void>
  signOut: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)
