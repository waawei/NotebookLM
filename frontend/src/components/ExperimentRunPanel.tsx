import { useEffect } from 'react'
import { modelingApi, type ExperimentRun } from '../services/api'

export default function ExperimentRunPanel({ projectId, experiments, onExecute, onChanged }: { projectId: string; experiments: ExperimentRun[]; onExecute: (experimentId: string) => void; onChanged: () => void }) {
  const shouldPoll = experiments.some((item) => item.status === 'prepared' || item.status === 'running')
  useEffect(() => {
    if (!shouldPoll) return undefined
    const timer = window.setInterval(() => { void modelingApi.listExperiments(projectId).then(onChanged).catch(() => undefined) }, 1500)
    return () => window.clearInterval(timer)
  }, [projectId, shouldPoll, onChanged])
  return <section className="rounded border border-gray-200 p-4 dark:border-gray-800">
    <h2 className="text-sm font-semibold">Experiments</h2>
    <div className="mt-3 space-y-2">{experiments.map((experiment) => <article key={experiment.experiment_id} className="rounded border border-gray-200 p-3 text-sm dark:border-gray-800"><div className="flex items-center justify-between gap-2"><span>{experiment.experiment_id} · {experiment.config.model.kind} · {experiment.status}</span>{experiment.status === 'prepared' && <button type="button" onClick={() => onExecute(experiment.experiment_id)} className="rounded bg-blue-600 px-2 py-1 text-xs text-white">Run</button>}</div><p className="mt-1 text-xs">Seed: {experiment.config.seed} | Exit: {experiment.exit_code ?? '—'} | Error: {experiment.error_code ?? '—'}</p><p className="mt-1 text-xs">Metrics: {experiment.config.metrics.map((metric) => `${metric.name} (${metric.direction})`).join(', ') || 'Pending'}</p>{experiment.artifacts?.filter((artifact) => artifact.artifact_type === 'experiment_figure').map((artifact) => <p key={artifact.artifact_id} className="mt-1 text-xs">Figure artifact: {artifact.artifact_id}</p>)}</article>)}</div>
  </section>
}
