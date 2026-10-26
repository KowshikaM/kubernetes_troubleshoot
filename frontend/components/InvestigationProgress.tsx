'use client'

import { useEffect, useState } from 'react'

const INVESTIGATION_STEPS = [
  'Checking Pods',
  'Reading Logs',
  'Analyzing Events',
  'Inspecting Deployments',
  'Checking Networking',
  'AI Reasoning',
  'Root Cause Found',
]

export function InvestigationProgress() {
  const [completedSteps, setCompletedSteps] = useState<string[]>([])

  useEffect(() => {
    let currentStep = 0

    const interval = setInterval(() => {
      if (currentStep < INVESTIGATION_STEPS.length) {
        setCompletedSteps((prev) => [...prev, INVESTIGATION_STEPS[currentStep]])
        currentStep++
      } else {
        clearInterval(interval)
      }
    }, 1500)

    return () => clearInterval(interval)
  }, [])

  return (
    <section className="space-y-4 rounded-lg border border-slate-800 bg-slate-900/50 p-6 backdrop-blur">
      <h2 className="text-lg font-semibold">Investigation Progress</h2>

      <div className="space-y-2">
        {INVESTIGATION_STEPS.map((step) => {
          const isCompleted = completedSteps.includes(step)
          const isActive = completedSteps[completedSteps.length - 1] === step

          return (
            <div
              key={step}
              className={`flex items-center gap-3 px-3 py-2 rounded transition-colors ${
                isCompleted || isActive ? 'bg-slate-800' : 'text-slate-500'
              }`}
            >
              <div
                className={`flex h-5 w-5 items-center justify-center rounded-full transition-colors ${
                  isCompleted
                    ? 'bg-green-600'
                    : isActive
                      ? 'animate-spin bg-sky-600'
                      : 'border border-slate-600'
                }`}
              >
                {isCompleted && (
                  <span className="text-xs font-bold text-white">✓</span>
                )}
              </div>
              <span className={isActive ? 'font-medium' : ''}>{step}</span>
            </div>
          )
        })}
      </div>
    </section>
  )
}
