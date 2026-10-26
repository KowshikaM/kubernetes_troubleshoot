'use client'

import { useAuth } from '@/app/context/AuthContext'
import { insforge } from '@/lib/insforge'
import { useRouter } from 'next/navigation'
import { FormEvent, useState } from 'react'

type AuthStep = 'auth' | 'verify'

export default function SignUpPage() {
  const router = useRouter()
  const { verifyEmail: contextVerifyEmail } = useAuth()
  const [step, setStep] = useState<AuthStep>('auth')
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

      if (data?.requireEmailVerification) {
        setVerifyMethod('code')
        setStep('verify')
        setPassword('')
        setError('')
      } else if (data?.accessToken) {
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
    } else {
      handleSignUp(e)
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
                : 'Create an account to continue'}
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
                  <label htmlFor="verification-code" className="block text-sm font-medium text-slate-300 mb-2">
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
              {loading ? 'Loading...' : step === 'verify' ? 'Verify Code' : 'Sign Up'}
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

          <div className="text-center">
            <button
              type="button"
              onClick={() => router.push('/login')}
              className="text-sm text-sky-400 hover:text-sky-300"
            >
              Already have an account? Sign in
            </button>
          </div>
        </div>
      </section>
    </main>
  )
}
