'use client'

import { useAuth } from '@/app/context/AuthContext'
import { insforge } from '@/lib/insforge'
import { useRouter } from 'next/navigation'
import { FormEvent, useState } from 'react'

type AuthStep = 'auth' | 'verify'
type AuthMode = 'signup' | 'signin'

export default function LoginPage() {
  const router = useRouter()
  const { signIn: contextSignIn, verifyEmail: contextVerifyEmail } = useAuth()
  const [step, setStep] = useState<AuthStep>('auth')
  const [mode, setMode] = useState<AuthMode>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [verificationCode, setVerificationCode] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [verifyMethod, setVerifyMethod] = useState<'code' | 'link' | null>(null)

  const handleSignUp = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const { data, error: signUpError } = await insforge.auth.signUp({
        email,
        password,
        redirectTo: `${typeof window !== 'undefined' ? window.location.origin : ''}/login`,
      })

      if (signUpError) {
        setError(signUpError.message)
        setLoading(false)
        return
      }

      // Check if email verification is required
      if (data?.requireEmailVerification) {
        // Move to verification step (assumes code-based verification)
        setVerifyMethod('code')
        setStep('verify')
        setPassword('') // Clear password after signup for security
        setError('')
      } else if (data?.accessToken) {
        // No verification required — user is already signed in
        router.push('/')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign up failed')
      setLoading(false)
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyEmail = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await contextVerifyEmail(email, verificationCode)
      // Successfully verified and signed in
      router.push('/')
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Verification failed'
      if (errorMsg.includes('400') || errorMsg.includes('expired')) {
        setError('Invalid or expired verification code. Please try again.')
      } else {
        setError(errorMsg)
      }
      setLoading(false)
    } finally {
      setLoading(false)
    }
  }

  const handleSignIn = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await contextSignIn(email, password)
      // Successfully signed in, redirect to dashboard
      router.push('/')
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Sign in failed'
      if (errorMsg.includes('403') || errorMsg.includes('not verified')) {
        setError('Email not verified. Please check your email for a verification link.')
      } else {
        setError(errorMsg)
      }
      setLoading(false)
    } finally {
      setLoading(false)
    }
  }

  const handleResendVerification = async () => {
    setError('')
    setLoading(true)

    try {
      const { error: resendError } = await insforge.auth.resendVerificationEmail({
        email,
        redirectTo: `${typeof window !== 'undefined' ? window.location.origin : ''}/login`,
      })

      if (resendError) {
        setError(resendError.message)
      } else {
        setError('Verification email resent. Check your inbox.')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resend verification email')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e: FormEvent) => {
    if (step === 'verify') {
      handleVerifyEmail(e)
    } else if (mode === 'signup') {
      handleSignUp(e)
    } else {
      handleSignIn(e)
    }
  }

  const toggleMode = () => {
    setError('')
    setEmail('')
    setPassword('')
    setVerificationCode('')
    setMode(mode === 'signup' ? 'signin' : 'signup')
    if (mode === 'signup') {
      router.push('/login')
    } else {
      router.push('/signup')
    }
  }

  const backToAuth = () => {
    setStep('auth')
    setVerificationCode('')
    setError('')
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-slate-950 px-6 text-white">
      <section className="w-full max-w-md">
        <div className="space-y-8">
          <div className="text-center">
            <h1 className="text-3xl font-bold tracking-tight">AI Kubernetes Agent</h1>
            <p className="mt-2 text-sm text-slate-400">
              {step === 'verify'
                ? 'Enter the 6-digit verification code from your email'
                : mode === 'signup'
                  ? 'Create an account to continue'
                  : 'Sign in to your account'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {step === 'verify' && verifyMethod === 'code' ? (
              <>
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                    Email
                  </label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    disabled
                    className="w-full rounded-lg bg-slate-700 px-4 py-2 text-slate-400 placeholder-slate-500"
                  />
                </div>

                <div>
                  <label
                    htmlFor="verification-code"
                    className="block text-sm font-medium text-slate-300 mb-2"
                  >
                    Verification Code
                  </label>
                  <input
                    id="verification-code"
                    type="text"
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    required
                    placeholder="000000"
                    className="w-full rounded-lg bg-slate-800 px-4 py-2 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-400"
                    maxLength={6}
                    inputMode="numeric"
                  />
                  <p className="mt-2 text-xs text-slate-400">
                    Check your email inbox (and spam folder) for the 6-digit code
                  </p>
                </div>
              </>
            ) : (
              <>
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                    Email
                  </label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full rounded-lg bg-slate-800 px-4 py-2 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-400"
                    placeholder="you@example.com"
                  />
                </div>

                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
                    Password
                  </label>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full rounded-lg bg-slate-800 px-4 py-2 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-400"
                    placeholder="••••••••"
                  />
                </div>
              </>
            )}

            {error && (
              <div className={`rounded-lg px-3 py-2 text-sm ${
                error.includes('resent') || error.includes('verification link')
                  ? 'bg-sky-900 bg-opacity-50 text-sky-200'
                  : 'bg-red-900 bg-opacity-50 text-red-200'
              }`}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-sky-600 px-4 py-2 font-semibold text-white transition-colors hover:bg-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-400 focus:ring-offset-2 focus:ring-offset-slate-950 disabled:opacity-50"
            >
              {loading
                ? 'Loading...'
                : step === 'verify'
                  ? 'Verify Code'
                  : mode === 'signup'
                    ? 'Sign Up'
                    : 'Sign In'}
            </button>
          </form>

          {step === 'verify' && verifyMethod === 'code' && (
            <div className="space-y-3 text-center">
              <button
                type="button"
                onClick={handleResendVerification}
                disabled={loading}
                className="w-full text-sm text-sky-400 hover:text-sky-300 disabled:opacity-50"
              >
                Didn't receive the code? Resend
              </button>
              <button
                type="button"
                onClick={backToAuth}
                className="block w-full text-sm text-slate-400 hover:text-slate-300"
              >
                Back to sign up
              </button>
            </div>
          )}

          {step === 'auth' && (
            <div className="text-center">
              <button
                type="button"
                onClick={toggleMode}
                className="text-sm text-sky-400 hover:text-sky-300"
              >
                {mode === 'signup' ? 'Already have an account? Sign in' : "Don't have an account? Sign up"}
              </button>
            </div>
          )}
        </div>
      </section>
    </main>
  )
}
