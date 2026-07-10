import { useEffect, useState } from 'react'
import { AlertCircle, CheckCircle2, Loader2, PlayCircle } from 'lucide-react'
import { agentsApi, type AgentRun } from '../services/api'
import { useStore } from '../store/useStore'

const statusLabel = {
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
}

export default function TaskProgressCards() {
  const [runs, setRuns] = useState<AgentRun[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const { setPreviewTarget, setActiveModule } = useStore()

  useEffect(() => {
    let isMounted = true
    setIsLoading(true)
    agentsApi.listRuns()
      .then((data) => {
        if (isMounted) setRuns((data.runs || []).slice(0, 6))
      })
      .catch((error) => {
        console.error('Failed to load task progress:', error)
      })
      .finally(() => {
        if (isMounted) setIsLoading(false)
      })

    return () => {
      isMounted = false
    }
  }, [])

  return (
    <section aria-labelledby="task-progress-heading" className="space-y-2">
      <h3 id="task-progress-heading" className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        Tasks
      </h3>
      {isLoading ? (
        <div className="flex items-center gap-2 rounded-lg border border-[#e2e1de] bg-white p-3 text-xs text-slate-500 dark:border-gray-800 dark:bg-gray-900">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading tasks
        </div>
      ) : runs.length === 0 ? (
        <div className="rounded-lg border border-[#e2e1de] bg-white p-3 text-xs text-slate-500 dark:border-gray-800 dark:bg-gray-900">
          No generated tasks yet
        </div>
      ) : (
        <div className="space-y-2">
          {runs.map((run) => {
            const Icon = run.status === 'completed' ? CheckCircle2 : run.status === 'failed' ? AlertCircle : Loader2
            return (
              <article
                key={run.run_id}
                data-testid={`task-card-${run.run_id}`}
                className="rounded-lg border border-[#e2e1de] bg-white p-3 shadow-sm dark:border-gray-800 dark:bg-gray-900"
              >
                <div className="flex items-start gap-3">
                  <div className={`mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-md ${
                    run.status === 'completed'
                      ? 'bg-green-50 text-green-700'
                      : run.status === 'failed'
                        ? 'bg-red-50 text-red-700'
                        : 'bg-blue-50 text-blue-700'
                  }`}>
                    <Icon className={`h-4 w-4 ${run.status === 'running' ? 'animate-spin' : ''}`} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <p className="truncate text-sm font-semibold text-slate-950 dark:text-slate-100">{run.skill_id}</p>
                      <span className="rounded-full bg-[#f5f4f3] px-2 py-0.5 text-[11px] font-semibold text-slate-600 dark:bg-gray-800 dark:text-gray-300">
                        {statusLabel[run.status]}
                      </span>
                    </div>
                    <p className="mt-1 line-clamp-2 text-xs text-slate-500 dark:text-slate-400">
                      {run.error || run.input_payload.request || 'Agent task'}
                    </p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {run.status === 'completed' && run.output_id && (
                        <button
                          type="button"
                          aria-label={`Open artifact for ${run.skill_id}`}
                          onClick={() => setPreviewTarget({ type: 'output', id: run.output_id!, title: `${run.skill_id} output` })}
                          className="inline-flex items-center gap-1 rounded-md border border-blue-100 bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700 hover:bg-blue-100"
                        >
                          <PlayCircle className="h-3.5 w-3.5" />
                          Open artifact
                        </button>
                      )}
                      <button
                        type="button"
                        aria-label={`View run ${run.skill_id}`}
                        onClick={() => setActiveModule('agents')}
                        className="rounded-md border border-[#e2e1de] bg-white px-2 py-1 text-xs font-semibold text-slate-600 hover:bg-[#f5f4f3] dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-800"
                      >
                        View run
                      </button>
                    </div>
                  </div>
                </div>
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}
