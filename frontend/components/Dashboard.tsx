'use client'

import { useAuth } from '@/app/context/AuthContext'
import { InvestigateButton } from '@/components/InvestigateButton'
import { InvestigationHistory } from '@/components/InvestigationHistory'
import { InvestigationProgress } from '@/components/InvestigationProgress'
import { RootCauseCard } from '@/components/RootCauseCard'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { useBackendAPI } from '@/hooks/useBackendAPI'

interface Diagnosis {
  root_cause: string
  explanation: string
  fix: string
  kubectl_commands: string[]
  confidence: number
}

interface InvestigationState {
  status: 'idle' | 'investigating' | 'complete' | 'error'
  diagnosis: Diagnosis | null
  error: string | null
}

interface ClusterInfo {
  name: string
  current: boolean
}

interface ClusterResponse {
  clusters?: ClusterInfo[]
}

export function Dashboard() {
  const { user, loading, signOut, isAuthenticated } = useAuth()
  const router = useRouter()
  const [investigation, setInvestigation] = useState<InvestigationState>({
    status: 'idle',
    diagnosis: null,
    error: null,
  })

  const { call } = useBackendAPI()
  const [clusters, setClusters] = useState<Array<{name:string,current:boolean}>>([])
  const [selectedCluster, setSelectedCluster] = useState<string | null>(null)
  const [seedProfile, setSeedProfile] = useState<'good'|'bad'|'mixed'>('good')
  const [seeding, setSeeding] = useState(false)

  useEffect(() => {
    ;(async () => {
      try {
        const res = await call<ClusterResponse>('/clusters', 'GET')
        setClusters(res.clusters || [])
        if (res.clusters && res.clusters.length) {
          const cur = res.clusters.find((x) => x.current)
          setSelectedCluster(cur ? cur.name : res.clusters[0].name)
        }
      } catch (err) {
        // ignore initially
        console.debug('Failed to load clusters', err)
      }
    })()
  }, [call])

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/login')
    }
  }, [loading, isAuthenticated, router])

  if (loading) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center bg-slate-950 text-white">
        <p>Loading...</p>
      </main>
    )
  }

  if (!user) {
    return null
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur">
        <div className="mx-auto max-w-4xl px-6 py-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">AI Kubernetes Agent</h1>
            <p className="mt-1 text-sm text-slate-400">Troubleshoot your cluster with AI</p>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-400">{user.email}</span>
            <button
              onClick={signOut}
              className="rounded px-3 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800 transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="mx-auto max-w-4xl px-6 py-12 space-y-12">
        {/* Investigation CTA Section */}
        <section className="space-y-6">
          <div>
            <h2 className="text-xl font-semibold mb-2">Investigate Cluster</h2>
            <p className="text-slate-400">Click below to run a comprehensive cluster analysis</p>
          </div>

          {/* Cluster selector and seed controls */}
          <div className="flex items-center gap-3 mb-4">
            <label className="text-sm text-slate-400">Select Cluster:</label>
            <select
              value={selectedCluster ?? ''}
              onChange={(e) => setSelectedCluster(e.target.value)}
              className="rounded bg-slate-800 px-3 py-2 text-sm"
            >
              <option value="">(default)</option>
              {clusters.map((c) => (
                <option key={c.name} value={c.name}>
                  {c.name} {c.current ? '(current)' : ''}
                </option>
              ))}
            </select>

            <button
              onClick={async () => {
                try {
                  const res = await call<ClusterResponse>('/clusters', 'GET')
                  setClusters(res.clusters || [])
                  if (res.clusters && res.clusters.length) {
                    const cur = res.clusters.find((x) => x.current)
                    setSelectedCluster(cur ? cur.name : res.clusters[0].name)
                  }
                } catch (err) {
                  console.error(err)
                  alert('Failed to fetch clusters')
                }
              }}
              className="rounded bg-slate-700 px-3 py-2 text-sm text-white hover:bg-slate-600"
            >
              Refresh clusters
            </button>

            <div className="ml-4 flex items-center gap-2">
              <select
                value={seedProfile}
                onChange={(e) => setSeedProfile(e.target.value as any)}
                className="rounded bg-slate-800 px-2 py-2 text-sm"
              >
                <option value="good">Good (healthy)</option>
                <option value="bad">Bad (failing)</option>
                <option value="mixed">Mixed</option>
              </select>
              <button
                onClick={async () => {
                  setSeeding(true)
                  try {
                    const res = await call<{ outputs?: unknown[] }>('/clusters/seed', 'POST', {
                      profile: seedProfile,
                      context: selectedCluster,
                    })
                    alert('Seeded cluster: ' + JSON.stringify(res.outputs || res))
                  } catch (err) {
                    console.error(err)
                    alert('Failed to seed cluster')
                  } finally {
                    setSeeding(false)
                  }
                }}
                disabled={seeding}
                className="rounded bg-blue-600 px-3 py-2 text-sm text-white hover:bg-blue-500 disabled:opacity-50"
              >
                {seeding ? 'Seeding...' : 'Seed cluster'}
              </button>
            </div>
          </div>

          <InvestigateButton
            context={selectedCluster}
            onStart={() => setInvestigation({ status: 'investigating', diagnosis: null, error: null })}
            onComplete={(diagnosis) => setInvestigation({ status: 'complete', diagnosis, error: null })}
            onError={(error) => setInvestigation({ status: 'error', diagnosis: null, error })}
          />
        </section>

        {/* Investigation Progress Section */}
        {investigation.status === 'investigating' && (
          <InvestigationProgress />
        )}

        {/* Root Cause Card */}
        {investigation.status === 'complete' && investigation.diagnosis && (
          <RootCauseCard diagnosis={investigation.diagnosis} />
        )}

        {/* Error Message */}
        {investigation.status === 'error' && investigation.error && (
          <div className="rounded-lg border border-red-800 bg-red-900/20 p-4">
            <p className="text-red-200">{investigation.error}</p>
          </div>
        )}

        {/* Investigation History Section */}
        <InvestigationHistory />
      </div>
    </main>
  )
}
