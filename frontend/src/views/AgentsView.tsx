import { useEffect, useState } from 'react'
import { AlertCircle, Bot, CheckCircle2, Loader2, RefreshCw } from 'lucide-react'
import { agentsApi, type AgentRun } from '../services/api'

export default function AgentsView() {
  const [runs, setRuns] = useState<AgentRun[]>([])
  const [loading, setLoading] = useState(false)
  const loadRuns = async () => { setLoading(true); try { setRuns((await agentsApi.listRuns()).runs) } finally { setLoading(false) } }
  useEffect(() => { void loadRuns() }, [])
  useEffect(() => {
    if (!runs.some((run) => run.status === 'running')) return
    const timer = window.setInterval(() => { void loadRuns() }, 1500)
    return () => window.clearInterval(timer)
  }, [runs])
  return <div className="h-full overflow-y-auto bg-gray-100 p-6 dark:bg-gray-950"><div className="mx-auto max-w-4xl"><div className="mb-6 flex items-center justify-between"><div><h2 className="text-xl font-semibold text-gray-950 dark:text-gray-100">Agents</h2><p className="text-sm text-gray-500">Every run exposes its status, steps, errors, and output link.</p></div><button onClick={loadRuns} className="rounded-lg border border-gray-200 p-2 dark:border-gray-700" aria-label="Refresh runs"><RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /></button></div><div className="space-y-4">{runs.map((run) => <article key={run.run_id} className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900"><div className="flex items-start justify-between"><div><p className="font-semibold text-gray-950 dark:text-gray-100">{run.skill_id}</p><p className="text-xs text-gray-500">{run.run_id}</p></div><Status status={run.status} /></div>{run.error && <p className="mt-3 flex gap-2 text-sm text-red-600"><AlertCircle className="h-4 w-4" />{run.error}</p>}<ol className="mt-4 space-y-2 border-l border-gray-200 pl-4 dark:border-gray-700">{run.steps.map((step) => <li key={step.step_id} className="text-sm text-gray-700 dark:text-gray-200"><span className="font-medium">{step.title}</span><span className="ml-2 text-xs text-gray-500">{step.kind}</span></li>)}</ol>{run.output_id && <p className="mt-4 text-sm text-blue-600">Persisted output: {run.output_id}</p>}</article>)}</div>{!loading && runs.length === 0 && <div className="py-16 text-center text-sm text-gray-500"><Bot className="mx-auto mb-3 h-10 w-10" />No agent runs yet.</div>}</div></div>
}

function Status({ status }: { status: AgentRun['status'] }) { if (status === 'completed') return <span className="flex items-center gap-1 text-sm text-green-600"><CheckCircle2 className="h-4 w-4" />Completed</span>; if (status === 'failed') return <span className="text-sm text-red-600">Failed</span>; return <span className="flex items-center gap-1 text-sm text-blue-600"><Loader2 className="h-4 w-4 animate-spin" />Running</span> }
