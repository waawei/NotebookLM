import { useState } from 'react'
import { modelingApi, type ApprovalRequest, type ExecutionBatch } from '../services/api'

export default function ExperimentApprovalCard({ projectId, approval, batch, canDecide = true, onDecided }: {
  projectId: string
  approval: ApprovalRequest
  batch: ExecutionBatch
  canDecide?: boolean
  onDecided: () => void | Promise<void>
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const decide = async (decision: 'approved' | 'changes_requested') => {
    setBusy(true)
    setError('')
    try {
      await modelingApi.decideApproval(projectId, approval.approval_id, { decision, payload_hash: approval.payload_hash, comment: decision === 'changes_requested' ? 'Please revise the experiment.' : '' })
      await onDecided()
    } catch {
      setError('Unable to record execution approval.')
    } finally { setBusy(false) }
  }
  return <section className="rounded border border-amber-300 bg-amber-50 p-4 dark:border-amber-900 dark:bg-amber-950">
    <h2 className="text-sm font-semibold">Experiment execution approval</h2>
    <p className="mt-1 break-all text-xs">Approval hash: {approval.payload_hash}</p>
    <p className="break-all text-xs">Code hash: {batch.code_hash}</p>
    <p className="mt-1 break-all text-xs">Inputs: {Object.entries(batch.input_hashes).map(([path, hash]) => `${path} (${hash})`).join(', ') || 'no registered inputs'}</p>
    <p className="break-all text-xs">Dependency lock hash: {batch.source_hashes['requirements.txt'] || 'No generated requirements lock'}</p>
    <pre className="mt-1 overflow-auto text-xs">{batch.dependency_lock || 'No generated requirements lock'}</pre>
    <p className="break-all text-xs">Dependency diff: {batch.dependency_diff.join(', ') || 'No dependency changes'}</p>
    <p className="mt-2 text-xs">Timeout: {batch.timeout_seconds}s | Output cap: {batch.max_output_bytes} bytes | Network: {batch.network_allowed ? 'Allowed for this batch' : 'Denied'}</p>
    <ul className="mt-2 list-disc pl-5 text-xs">{batch.commands.map((command) => <li key={command.join('\u0000')}><code>{command.join(' ')}</code></li>)}</ul>
    {error && <p role="alert" className="mt-2 text-sm text-red-700">{error}</p>}
    <div className="mt-3 flex gap-2"><button type="button" disabled={busy || !canDecide} onClick={() => void decide('approved')} className="rounded bg-green-700 px-3 py-2 text-sm text-white">Approve execution</button><button type="button" disabled={busy || !canDecide} onClick={() => void decide('changes_requested')} className="rounded border px-3 py-2 text-sm">Request changes</button></div>
  </section>
}
