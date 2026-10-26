'use client'

import { insforge } from '@/lib/insforge'
import {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useState,
} from 'react'

interface AuthContextType {
  user: any | null
  loading: boolean
  signUp: (email: string, password: string) => Promise<void>
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  verifyEmail: (email: string, otp: string) => Promise<void>
  isAuthenticated: boolean
  setUser: (user: any) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<any | null>(null)
  const [loading, setLoading] = useState(true)

  // Check if user is already authenticated on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const { data } = await insforge.auth.getCurrentUser()
        setUser(data.user || null)
      } catch (error) {
        console.log('No authenticated user')
        setUser(null)
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [])

  const signUp = async (email: string, password: string) => {
    const { data, error } = await insforge.auth.signUp({
      email,
      password,
    })

    if (error) throw new Error(error.message)
    // User will need to verify email before being set as authenticated
    // This is handled in the login page
  }

  const signIn = async (email: string, password: string) => {
    const { data, error } = await insforge.auth.signInWithPassword({
      email,
      password,
    })

    if (error) throw new Error(error.message)
    setUser(data?.user || null)
  }

  const signOut = async () => {
    const { error } = await insforge.auth.signOut()
    if (error) throw new Error(error.message)
    setUser(null)
  }

  const verifyEmail = async (email: string, otp: string) => {
    const { data, error } = await insforge.auth.verifyEmail({
      email,
      otp,
    })

    if (error) throw new Error(error.message)
    setUser(data?.user || null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        signUp,
        signIn,
        signOut,
        verifyEmail,
        isAuthenticated: !!user,
        setUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
