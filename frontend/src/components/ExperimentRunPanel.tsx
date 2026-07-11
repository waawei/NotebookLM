import { useEffect, useState } from 'react'
import { modelingApi, type ExperimentRun } from '../services/api'

interface ExperimentRunPanelProps {
  projectId: string
  experiments: ExperimentRun[]
  canExecute?: boolean
  onExecute: (experimentId: string) => void
  onChanged: () => void
}

export default function ExperimentRunPanel({ projectId, experiments, canExecute = true, onExecute, onChanged }: ExperimentRunPanelProps) {
  const [evidence, setEvidence] = useState<Record<string, unknown>>({})
  const shouldPoll = experiments.some((item) => item.status === 'prepared' || item.status === 'running')

  useEffect(() => {
    if (!shouldPoll) return undefined
    const timer = window.setInterval(() => { void modelingApi.listExperiments(projectId).then(onChanged).catch(() => undefined) }, 1500)
    return () => window.clearInterval(timer)
  }, [projectId, shouldPoll, onChanged])

  useEffect(() => {
    const artifacts = experiments.flatMap((experiment) => experiment.artifacts || []).filter((artifact) => artifact.artifact_type === 'experiment_metrics' || artifact.artifact_type === 'experiment_log')
    if (artifacts.length === 0) return
    void Promise.all(artifacts.map(async (artifact) => [artifact.artifact_id, (await modelingApi.getArtifact(projectId, artifact.artifact_id)).content] as const)).then((items) => setEvidence(Object.fromEntries(items))).catch(() => undefined)
  }, [projectId, experiments])

  return <section className="rounded border border-gray-200 p-4 dark:border-gray-800">
    <h2 className="text-sm font-semibold">Experiments</h2>
    <div className="mt-3 space-y-2">{experiments.map((experiment) => <article id={`experiment-${experiment.experiment_id}`} key={experiment.experiment_id} className="rounded border border-gray-200 p-3 text-sm dark:border-gray-800"><div className="flex items-center justify-between gap-2"><span>{experiment.experiment_id} / {experiment.config.model.kind} / {experiment.status}</span>{experiment.status === 'prepared' && <button type="button" disabled={!canExecute} onClick={() => onExecute(experiment.experiment_id)} className="rounded bg-blue-600 px-2 py-1 text-xs text-white disabled:bg-gray-400">Run</button>}</div><p className="mt-1 text-xs">Seed: {experiment.config.seed} | Exit: {experiment.exit_code ?? '-'} | Error: {experiment.error_code ?? '-'}</p><p className="mt-1 text-xs">Configured metrics: {experiment.config.metrics.map((metric) => `${metric.name} (${metric.direction})`).join(', ') || 'Pending'}</p>{experiment.artifacts?.filter((artifact) => artifact.artifact_type === 'experiment_metrics').map((artifact) => <pre key={artifact.artifact_id} className="mt-1 overflow-auto text-xs">{JSON.stringify(evidence[artifact.artifact_id] || 'Metrics pending')}</pre>)}{experiment.artifacts?.filter((artifact) => artifact.artifact_type === 'experiment_log').map((artifact) => <pre key={artifact.artifact_id} className="mt-1 max-h-32 overflow-auto text-xs">{String(evidence[artifact.artifact_id] || 'Log pending')}</pre>)}{experiment.artifacts?.filter((artifact) => artifact.artifact_type === 'experiment_figure').map((artifact) => <a key={artifact.artifact_id} href={`/api/modeling/projects/${projectId}/artifacts/${artifact.artifact_id}`} className="mt-1 block text-xs text-blue-700 underline">Figure artifact: {artifact.artifact_id}</a>)}</article>)}</div>
  </section>
}
