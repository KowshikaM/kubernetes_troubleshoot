"use client";

import { getAuthToken } from "@/hooks/useBackendAPI";
import { useAuth } from "@/app/context/AuthContext";
import { useRouter } from "next/navigation";
import { useState } from "react";

interface Diagnosis {
  root_cause: string
  explanation: string
  fix: string
  kubectl_commands: string[]
  confidence: number
}

interface InvestigateButtonProps {
  onStart?: () => void
  onComplete?: (diagnosis: Diagnosis) => void
  onError?: (error: string) => void
  // Optional kube context name to run the investigation against
  context?: string | null
}

export function InvestigateButton({ onStart, onComplete, onError, context }: InvestigateButtonProps) {
  const { isAuthenticated } = useAuth()
  const router = useRouter()
  const [loading, setLoading] = useState(false)

  async function handleClick() {
    if (!isAuthenticated) {
      router.push("/login")
      return
    }

    setLoading(true)
    onStart?.()

    let es: EventSource | null = null

    try {
      const token = await getAuthToken()
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      }

      if (token) {
        headers['Authorization'] = token
      }

      // Start SSE subscription using the user id derived from the token (format: "user:<id>")
      let userId: string | null = null
      if (token && token.includes(':')) {
        userId = token.split(':', 2)[1]
      }

      if (userId) {
        try {
          es = new EventSource(`${process.env.NEXT_PUBLIC_API_BASE_URL}/progress/stream/${userId}`)
          es.onmessage = (ev) => {
            try {
              const msg = JSON.parse(ev.data)
              if (msg?.type === 'done' && msg?.diagnosis) {
                onComplete?.(msg.diagnosis)
                if (es) es.close()
                setLoading(false)
              }
            } catch (e) {
              // ignore malformed messages
            }
          }
          es.onerror = () => {
            // don't spam errors to users; close the connection on error
            if (es) es.close()
          }
        } catch (e) {
          // EventSource may not be available in non-browser env; ignore
        }
      }

      const payload: any = {}
      if ((typeof (context) !== 'undefined') && context) payload.context = context

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/investigate`,
        {
          method: "POST",
          headers,
          body: JSON.stringify(payload),
        }
      )

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`)
      }

      const data = await response.json()

      // If backend returns diagnosis immediately, use it; otherwise rely on SSE subscription
      if (data.status === "success" && data.diagnosis) {
        onComplete?.(data.diagnosis)
        if (es) es.close()
      } else if (data.status !== 'success') {
        onError?.(data.error || "Investigation failed")
        if (es) es.close()
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to investigate"
      onError?.(message)
    } finally {
      setLoading(false)
      if (es) es.close()
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={loading}
      className="rounded-lg bg-sky-600 px-6 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-400 focus:ring-offset-2 focus:ring-offset-slate-950 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {loading ? "Investigating..." : "Investigate Cluster"}
    </button>
  );
}


