/* eslint-disable react-refresh/only-export-components */

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { api } from './api'
import { clearStoredAuth, readStoredAuth, storeAuth, type StoredAuth } from './authStorage'

interface AuthContextValue {
  session: StoredAuth | null
  login: (researcher_id: string, password: string) => Promise<void>
  register: (researcher_id: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<StoredAuth | null>(() => readStoredAuth())
  const queryClient = useQueryClient()

  const logout = useCallback(() => {
    clearStoredAuth()
    setSession(null)
    queryClient.clear()
  }, [queryClient])

  useEffect(() => {
    window.addEventListener('research-auth-expired', logout)
    return () => window.removeEventListener('research-auth-expired', logout)
  }, [logout])

  const persistAuthentication = useCallback((response: {
    access_token: string
    researcher_id: string
  }) => {
    const authenticated = {
      accessToken: response.access_token,
      researcher_id: response.researcher_id,
    }
    storeAuth(authenticated)
    setSession(authenticated)
  }, [])

  const authenticate = useCallback(async (researcher_id: string, password: string) => {
    persistAuthentication(await api.login(researcher_id, password))
  }, [persistAuthentication])

  const register = useCallback(async (researcher_id: string, password: string) => {
    persistAuthentication(await api.register(researcher_id, password))
  }, [persistAuthentication])

  const value = useMemo<AuthContextValue>(() => ({
    session,
    login: authenticate,
    register,
    logout,
  }), [authenticate, logout, register, session])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('AuthProvider is required.')
  return value
}
