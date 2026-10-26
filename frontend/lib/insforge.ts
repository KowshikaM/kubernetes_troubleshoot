import { createClient } from '@insforge/sdk'

const LOCAL_USERS_KEY = 'ai-kube-demo-users'
const LOCAL_SESSION_KEY = 'ai-kube-demo-session'
const LOCAL_OTP_KEY = 'ai-kube-demo-otp'

const baseUrl = process.env.NEXT_PUBLIC_INSFORGE_URL || ''
const anonKey = process.env.NEXT_PUBLIC_INSFORGE_ANON_KEY || ''
const useLocalAuth = process.env.NEXT_PUBLIC_USE_LOCAL_AUTH === 'true'

function readJson<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') return fallback
  try {
    const value = localStorage.getItem(key)
    return value ? (JSON.parse(value) as T) : fallback
  } catch {
    return fallback
  }
}

function writeJson<T>(key: string, value: T) {
  if (typeof window === 'undefined') return
  localStorage.setItem(key, JSON.stringify(value))
}

function generateUserId() {
  return `user-${Math.random().toString(36).slice(2, 10)}`
}

function generateOtp() {
  return String(Math.floor(100000 + Math.random() * 900000))
}

function createDemoAuth() {
  const auth = {
    signUp: async ({ email, password }: { email: string; password: string }) => {
      const users = readJson<Record<string, { email: string; password: string; id: string; verified: boolean }>>(LOCAL_USERS_KEY, {})
      const normalizedEmail = email.toLowerCase()
      const existing = users[normalizedEmail]

      if (existing) {
        const otp = generateOtp()
        writeJson(LOCAL_OTP_KEY, { email: normalizedEmail, otp })
        return {
          data: {
            user: { id: existing.id, email: existing.email },
            accessToken: null,
            requireEmailVerification: true,
          },
          error: null,
        }
      }

      const user = {
        id: generateUserId(),
        email: normalizedEmail,
        password,
        verified: false,
      }
      users[user.email] = user
      writeJson(LOCAL_USERS_KEY, users)

      const otp = generateOtp()
      writeJson(LOCAL_OTP_KEY, { email: user.email, otp })

      return {
        data: {
          user: { id: user.id, email: user.email },
          accessToken: null,
          requireEmailVerification: true,
        },
        error: null,
      }
    },

    signInWithPassword: async ({ email, password }: { email: string; password: string }) => {
      const users = readJson<Record<string, { email: string; password: string; id: string; verified: boolean }>>(LOCAL_USERS_KEY, {})
      const user = users[email.toLowerCase()]

      if (!user || user.password !== password) {
        return { data: null, error: { message: 'Invalid email or password' } }
      }

      if (!user.verified) {
        return { data: null, error: { message: 'Email not verified. Please verify your code first.' } }
      }

      const session = { id: user.id, email: user.email }
      writeJson(LOCAL_SESSION_KEY, session)
      return { data: { user: session, accessToken: 'local-demo-token' }, error: null }
    },

    getCurrentUser: async () => {
      const session = readJson<{ id: string; email: string } | null>(LOCAL_SESSION_KEY, null)
      return { data: { user: session }, error: null }
    },

    signOut: async () => {
      writeJson(LOCAL_SESSION_KEY, null)
      return { error: null }
    },

    verifyEmail: async ({ email, otp }: { email: string; otp?: string }) => {
      const users = readJson<Record<string, { email: string; password: string; id: string; verified: boolean }>>(LOCAL_USERS_KEY, {})
      const normalizedEmail = email.toLowerCase()
      const storedOtp = readJson<{ email: string; otp: string } | null>(LOCAL_OTP_KEY, null)

      if (!users[normalizedEmail]) {
        return { data: null, error: { message: 'User not found' } }
      }

      if (!storedOtp || storedOtp.email !== normalizedEmail || storedOtp.otp !== String(otp)) {
        return { data: null, error: { message: 'Invalid or expired verification code' } }
      }

      users[normalizedEmail].verified = true
      writeJson(LOCAL_USERS_KEY, users)

      const session = { id: users[normalizedEmail].id, email: users[normalizedEmail].email }
      writeJson(LOCAL_SESSION_KEY, session)
      writeJson(LOCAL_OTP_KEY, null)
      return { data: { user: session }, error: null }
    },

    resendVerificationEmail: async ({ email }: { email: string }) => {
      const users = readJson<Record<string, { email: string; password: string; id: string; verified: boolean }>>(LOCAL_USERS_KEY, {})
      const normalizedEmail = email.toLowerCase()
      const user = users[normalizedEmail]
      if (!user) {
        return { error: { message: 'User not found' } }
      }
      const otp = generateOtp()
      writeJson(LOCAL_OTP_KEY, { email: normalizedEmail, otp })
      return { error: null }
    },
  }

  return { auth }
}

const shouldUseLocalFallback =
  useLocalAuth ||
  !baseUrl ||
  !anonKey

export const insforge = shouldUseLocalFallback
  ? createDemoAuth()
  : createClient({
      baseUrl,
      anonKey,
    })
