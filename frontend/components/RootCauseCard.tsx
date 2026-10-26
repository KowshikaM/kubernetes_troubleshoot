'use client'

interface Diagnosis {
  root_cause: string
  explanation: string
  fix: string
  kubectl_commands: string[]
  confidence: number
}

interface RootCauseCardProps {
  diagnosis: Diagnosis
}

export function RootCauseCard({ diagnosis }: RootCauseCardProps) {
  return (
    <section className="space-y-6 rounded-lg border border-slate-800 bg-slate-900/50 p-6 backdrop-blur">
      <h2 className="text-lg font-semibold">Diagnosis Results</h2>

      {/* Root Cause */}
      <div className="space-y-2">
        <h3 className="text-sm font-medium text-slate-300">Root Cause</h3>
        <p className="text-lg font-semibold text-sky-400">{diagnosis.root_cause}</p>
      </div>

      {/* Explanation */}
      <div className="space-y-2">
        <h3 className="text-sm font-medium text-slate-300">Explanation</h3>
        <p className="text-slate-300 leading-relaxed">{diagnosis.explanation}</p>
      </div>

      {/* Suggested Fix */}
      <div className="space-y-2">
        <h3 className="text-sm font-medium text-slate-300">Suggested Fix</h3>
        <p className="text-slate-300 leading-relaxed">{diagnosis.fix}</p>
      </div>

      {/* kubectl Commands */}
      {diagnosis.kubectl_commands && diagnosis.kubectl_commands.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-slate-300">kubectl Command</h3>
          <div className="space-y-2">
            {diagnosis.kubectl_commands.map((cmd, idx) => (
              <div
                key={idx}
                className="rounded bg-slate-950 p-3 font-mono text-sm text-slate-200 overflow-x-auto"
              >
                {cmd}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Confidence Score */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-slate-300">Confidence Score</h3>
          <span className="text-2xl font-bold text-green-400">{diagnosis.confidence}%</span>
        </div>
        <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-sky-600 to-green-600 transition-all"
            style={{ width: `${diagnosis.confidence}%` }}
          />
        </div>
      </div>
    </section>
  )
}
