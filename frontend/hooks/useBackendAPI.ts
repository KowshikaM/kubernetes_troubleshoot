import { insforge } from '@/lib/insforge'
import { useCallback } from 'react'

/**
 * Get the current user's authentication token for API calls.
 * In local demo mode, this falls back to a browser session object.
 */
export async function getAuthToken(): Promise<string | null> {
  try {
    const { data } = await insforge.auth.getCurrentUser()
    if (data?.user?.id) {
      return `user:${data.user.id}`
    }
  } catch {
    // no-op: user is not authenticated in the current session
  }

  if (typeof window !== 'undefined') {
    try {
      const raw = localStorage.getItem('ai-kube-demo-session')
      if (!raw) return null
      const user = JSON.parse(raw)
      if (user?.id) return `user:${user.id}`
    } catch {
      return null
    }
  }

  return null
}

/**
 * Hook for making authenticated API calls to the backend
 */
export function useBackendAPI() {
  const call = useCallback(
    async <T,>(
      endpoint: string,
      method: string = 'GET',
      body?: unknown
    ): Promise<T> => {
      const token = await getAuthToken()
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      }

      if (token) {
        headers['Authorization'] = token
      }

      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8001'
      const response = await fetch(
        `${apiBaseUrl}${endpoint}`,
        {
          method,
          headers,
          body: body ? JSON.stringify(body) : undefined,
        }
      )

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`)
      }

      return response.json()
    },
    []
  )

  return { call }
}


