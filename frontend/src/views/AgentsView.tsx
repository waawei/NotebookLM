import { useEffect, useState } from 'react'
import { AlertCircle, Bot, CheckCircle2, Loader2, RefreshCw } from 'lucide-react'
import { agentsApi, type AgentRun } from '../services/api'

interface AgentsViewProps {
  onOpenOutput?: () => void
}

export default function AgentsView({ onOpenOutput }: AgentsViewProps) {
  const [runs, setRuns] = useState<AgentRun[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const loadRuns = async () => {
    setLoading(true)
    setError('')
    try {
      setRuns((await agentsApi.listRuns()).runs)
    } catch {
      setError('Unable to load agent runs. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const refreshActiveRuns = async (runIds: string[]) => {
    try {
      const refreshed = await Promise.all(runIds.map((runId) => agentsApi.getRun(runId)))
      const byId = new Map(refreshed.map((run) => [run.run_id, run]))
      setRuns((current) => current.map((run) => byId.get(run.run_id) || run))
    } catch {
      setError('Unable to refresh active runs. The latest saved state will remain visible.')
    }
  }

  useEffect(() => {
    void loadRuns()
  }, [])

  useEffect(() => {
    const activeIds = runs.filter((run) => run.status === 'running').map((run) => run.run_id)
    if (!activeIds.length) return
    const timer = window.setInterval(() => void refreshActiveRuns(activeIds), 1500)
    return () => window.clearInterval(timer)
  }, [runs])

  return (
    <div className="h-full overflow-y-auto bg-gray-100 p-6 dark:bg-gray-950">
      <div className="mx-auto max-w-4xl">
        <div className="mb-6 flex items-center justify-between gap-3">
          <div><h2 className="text-xl font-semibold text-gray-950 dark:text-gray-100">Agents</h2><p className="text-sm text-gray-500 dark:text-gray-400">Every run exposes saved status, steps, errors, and output.</p></div>
          <button onClick={() => void loadRuns()} className="rounded-lg border border-gray-200 p-2 dark:border-gray-700" aria-label="Refresh runs"><RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /></button>
        </div>

        {error && <div className="mb-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200"><AlertCircle className="h-4 w-4 shrink-0" />{error}</div>}
        {loading && runs.length === 0 ? <div className="flex justify-center gap-2 py-16 text-sm text-gray-500"><Loader2 className="h-4 w-4 animate-spin" />Loading runs</div> : <div className="space-y-4">
          {runs.map((run) => <article key={run.run_id} className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900">
            <div className="flex items-start justify-between gap-3"><div><p className="font-semibold text-gray-950 dark:text-gray-100">{run.skill_id}</p><p className="text-xs text-gray-500 dark:text-gray-400">{run.run_id}</p></div><Status status={run.status} /></div>
            {run.error && <p className="mt-3 flex gap-2 text-sm text-red-600 dark:text-red-300"><AlertCircle className="h-4 w-4 shrink-0" />{run.error}</p>}
            <ol className="mt-4 space-y-2 border-l border-gray-200 pl-4 dark:border-gray-700">{run.steps.map((step) => <li key={step.step_id} className="text-sm text-gray-700 dark:text-gray-200"><span className="font-medium">{step.title}</span><span className="ml-2 text-xs text-gray-500">{step.kind}</span></li>)}</ol>
            {run.output_id && <a href="#outputs" onClick={onOpenOutput} className="mt-4 inline-flex text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-300" aria-label="Open output">Open output</a>}
          </article>)}
        </div>}
        {!loading && runs.length === 0 && <div className="py-16 text-center text-sm text-gray-500"><Bot className="mx-auto mb-3 h-10 w-10" />No agent runs yet.</div>}
      </div>
    </div>
  )
}

function Status({ status }: { status: AgentRun['status'] }) {
  if (status === 'completed') return <span className="flex items-center gap-1 text-sm text-green-600 dark:text-green-300"><CheckCircle2 className="h-4 w-4" />Completed</span>
  if (status === 'failed') return <span className="text-sm text-red-600 dark:text-red-300">Failed</span>
  return <span className="flex items-center gap-1 text-sm text-blue-600 dark:text-blue-300"><Loader2 className="h-4 w-4 animate-spin" />Running</span>
}
