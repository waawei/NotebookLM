import type { ExperimentRun } from '../services/api'

export default function ExperimentRunPanel({ experiments, onExecute }: { experiments: ExperimentRun[]; onExecute: (experimentId: string) => void }) {
  return <section className="rounded border border-gray-200 p-4 dark:border-gray-800">
    <h2 className="text-sm font-semibold">Experiments</h2>
    <div className="mt-3 space-y-2">{experiments.map((experiment) => <article key={experiment.experiment_id} className="rounded border border-gray-200 p-3 text-sm dark:border-gray-800"><div className="flex items-center justify-between gap-2"><span>{experiment.experiment_id} · {experiment.config.model.kind} · {experiment.status}</span>{experiment.status === 'prepared' && <button type="button" onClick={() => onExecute(experiment.experiment_id)} className="rounded bg-blue-600 px-2 py-1 text-xs text-white">Run</button>}</div><p className="mt-1 text-xs">Seed: {experiment.config.seed} | Exit: {experiment.exit_code ?? '—'} | Error: {experiment.error_code ?? '—'}</p></article>)}</div>
  </section>
}
