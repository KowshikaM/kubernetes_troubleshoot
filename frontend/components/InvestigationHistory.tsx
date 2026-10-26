'use client'

import { useAuth } from '@/app/context/AuthContext'
import { getAuthToken } from '@/hooks/useBackendAPI'
import { useEffect, useState } from 'react'

interface HistoryEntry {
  id: string
  root_cause: string
  confidence: number
  created_at: string
  status: string
}

export function InvestigationHistory() {
  const { isAuthenticated } = useAuth()
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isAuthenticated) return

    const fetchHistory = async () => {
      setLoading(true)
      setError(null)

      try {
        const token = await getAuthToken()
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
        }

        if (token) {
          headers['Authorization'] = token
        }

        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE_URL}/investigations/history`,
          {
            method: 'GET',
            headers,
          }
        )

        if (!response.ok) {
          throw new Error(`Failed to fetch history: ${response.statusText}`)
        }

        const data = await response.json()

        if (data.status === 'success' && Array.isArray(data.data)) {
          setHistory(data.data)
        } else {
          setHistory([])
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch history')
        setHistory([])
      } finally {
        setLoading(false)
      }
    }

    fetchHistory()
  }, [isAuthenticated])

  return (
    <section className="space-y-4 rounded-lg border border-slate-800 bg-slate-900/50 p-6 backdrop-blur">
      <h2 className="text-lg font-semibold">Investigation History</h2>

      {error && (
        <div className="rounded bg-red-900/20 p-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-slate-400">Loading history...</p>
      ) : history.length === 0 ? (
        <p className="text-slate-400">No investigations yet. Click "Investigate Cluster" to start.</p>
      ) : (
        <div className="space-y-2">
          {history.map((entry) => (
            <div
              key={entry.id}
              className="flex items-center justify-between rounded bg-slate-800/50 p-4 hover:bg-slate-800 transition-colors"
            >
              <div className="flex-1">
                <p className="font-medium">{entry.root_cause}</p>
                <p className="text-sm text-slate-400">
                  {new Date(entry.created_at).toLocaleString()}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <p className="font-semibold text-sky-400">{entry.confidence}%</p>
                  <p className="text-xs text-slate-400">{entry.status}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}


