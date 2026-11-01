import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import type { Session } from '@supabase/supabase-js'
import { apiConfigured } from '../../lib/env'
import { getApiError, getData } from '../../lib/api'
import { supabase } from '../../lib/supabase'
import type { AccountStatus } from '../../lib/types'
import { AuthContext, type AuthContextValue } from './authContext'

async function fetchAccountStatus(session: Session): Promise<AccountStatus> {
  return getData<AccountStatus>('/auth/status', {
    headers: { Authorization: `Bearer ${session.access_token}` },
  })
}

export function AuthProvider({
  children,
  onSignOut,
}: {
  children: ReactNode
  onSignOut: () => void
}) {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(Boolean(supabase))
  const [accountStatus, setAccountStatus] = useState<AccountStatus | null>(null)
  const [statusError, setStatusError] = useState('')
  const sessionUserId = useRef<string | null>(null)

  useEffect(() => {
    if (!supabase) {
      setLoading(false)
      return
    }
    let active = true
    void supabase.auth.getSession().then(({ data, error }) => {
      if (!active) return
      if (error) {
        setStatusError(error.message)
        setLoading(false)
        return
      }
      sessionUserId.current = data.session?.user.id ?? null
      setSession(data.session)
      if (!data.session) setLoading(false)
    })
    const { data } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      if (sessionUserId.current && nextSession && sessionUserId.current !== nextSession.user.id) {
        onSignOut()
      }
      sessionUserId.current = nextSession?.user.id ?? null
      setSession(nextSession)
      setAccountStatus(null)
      setStatusError('')
      setLoading(Boolean(nextSession))
      if (!nextSession) onSignOut()
    })
    return () => {
      active = false
      data.subscription.unsubscribe()
    }
  }, [onSignOut])

  useEffect(() => {
    if (!session) {
      setAccountStatus(null)
      setStatusError('')
      setLoading(false)
      return
    }
    let active = true
    setLoading(true)
    setStatusError('')
    void fetchAccountStatus(session)
      .then((result) => {
        if (active) setAccountStatus(result)
      })
      .catch((error: unknown) => {
        if (!active) return
        setAccountStatus(null)
        setStatusError(getApiError(error))
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [session])

  const refreshAccountStatus = useCallback(async () => {
    if (!session) return
    setLoading(true)
    setStatusError('')
    try {
      setAccountStatus(await fetchAccountStatus(session))
    } catch (error) {
      setAccountStatus(null)
      setStatusError(getApiError(error))
      throw error
    } finally {
      setLoading(false)
    }
  }, [session])

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      loading,
      configured: Boolean(supabase) && apiConfigured,
      accountStatus,
      statusError,
      refreshAccountStatus,
      signOut: async () => {
        if (!supabase) return
        const { error } = await supabase.auth.signOut()
        if (error) throw error
        onSignOut()
      },
    }),
    [session, loading, accountStatus, statusError, refreshAccountStatus, onSignOut],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
