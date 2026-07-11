import { useState } from 'react'
import { RotateCcw, X } from 'lucide-react'
import { modelingApi, type ModelingRecovery } from '../services/api'

export default function ModelingRecoveryBanner({ recovery, onDismissed }: { recovery: ModelingRecovery; onDismissed: (recoveryId: string) => void }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const dismiss = async () => {
    setBusy(true)
    setError('')
    try {
      await modelingApi.dismissRecovery(recovery.recovery_id)
      onDismissed(recovery.recovery_id)
    } catch {
      setError('Unable to dismiss the recovery notice.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section role="status" className="border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-100">
      <div className="flex items-start gap-2">
        <RotateCcw className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
        <div className="min-w-0 flex-1">
          <h2 className="font-semibold">Recovered interrupted workflow</h2>
          <p className="mt-1">Recovered from <code>{recovery.from_state}</code> to safe stage <code>{recovery.to_state}</code>.</p>
          {recovery.interrupted_run_ids.length > 0 && <p className="mt-1">Interrupted run: {recovery.interrupted_run_ids.map((runId, index) => <span key={runId}>{index > 0 && ', '}<a className="underline" href={`#experiment-${runId}`}>{runId}</a></span>)}</p>}
          {error && <p role="alert" className="mt-2">{error}</p>}
        </div>
        <button type="button" aria-label="Dismiss recovery notice" title="Dismiss recovery notice" disabled={busy} onClick={() => void dismiss()} className="grid h-8 w-8 shrink-0 place-items-center rounded border border-amber-400 disabled:opacity-50">
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </section>
  )
}
