export interface StoredAuth {
  accessToken: string
  researcher_id: string
}

const AUTH_STORAGE_KEY = 'research-dashboard-auth'

export function readStoredAuth(): StoredAuth | null {
  const value = window.localStorage.getItem(AUTH_STORAGE_KEY)
  if (!value) return null
  try {
    const parsed = JSON.parse(value) as Partial<StoredAuth>
    if (typeof parsed.accessToken === 'string' && typeof parsed.researcher_id === 'string') {
      return { accessToken: parsed.accessToken, researcher_id: parsed.researcher_id }
    }
  } catch {
    // Invalid local state is treated as a signed-out session.
  }
  window.localStorage.removeItem(AUTH_STORAGE_KEY)
  return null
}

export function storeAuth(value: StoredAuth) {
  window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(value))
}

export function clearStoredAuth() {
  window.localStorage.removeItem(AUTH_STORAGE_KEY)
}
