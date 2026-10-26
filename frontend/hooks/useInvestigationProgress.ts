'use client'

import { insforge } from '@/lib/insforge'
import { useCallback, useEffect, useRef, useState } from 'react'

interface RealtimeProgressUpdate {
  step: string
  status: 'in_progress' | 'completed'
  timestamp: string
}

/**
 * Hook for listening to realtime investigation progress updates
 */
export function useInvestigationProgress(investigationId: string | null) {
  const [progress, setProgress] = useState<RealtimeProgressUpdate[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const channelRef = useRef<any>(null)

  // Subscribe to realtime updates
  useEffect(() => {
    if (!investigationId) return

    const subscribeToProgress = async () => {
      try {
        // Subscribe to the investigation progress channel
        // In production, this would subscribe to a realtime channel like:
        // const channel = insforge.realtime.subscribe(
        //   `investigations:${investigationId}`,
        //   { event: 'progress' }
        // )
        //
        // channel.on('progress', (payload) => {
        //   setProgress((prev) => [...prev, payload])
        // })
        //
        // channelRef.current = channel

        // For now, just mark as connected
        setIsConnected(true)
      } catch (error) {
        console.error('Failed to subscribe to progress updates:', error)
      }
    }

    subscribeToProgress()

    return () => {
      // Cleanup subscription on unmount
      if (channelRef.current) {
        // insforge.realtime.unsubscribe(channelRef.current)
      }
    }
  }, [investigationId])

  return { progress, isConnected }
}

/**
 * Publish a progress update to the realtime channel
 */
export async function publishInvestigationProgress(
  investigationId: string,
  update: RealtimeProgressUpdate
) {
  try {
    // In production, publish the update via InsForge realtime:
    // await insforge.realtime.publish(
    //   `investigations:${investigationId}`,
    //   { event: 'progress', data: update }
    // )
    
    return true
  } catch (error) {
    console.error('Failed to publish progress update:', error)
    return false
  }
}
