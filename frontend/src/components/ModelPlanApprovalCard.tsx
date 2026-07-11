import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import { modelingApi, type ApprovalRequest, type ModelPlan } from '../services/api'

interface ModelPlanApprovalCardProps {
  projectId: string
  approval: ApprovalRequest
  plan: ModelPlan
  onDecided: () => void | Promise<void>
}

export default function ModelPlanApprovalCard({ projectId, approval, plan, onDecided }: ModelPlanApprovalCardProps) {
  const [comment, setComment] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const decide = async (decision: 'approved' | 'changes_requested') => {
    const cleanComment = comment.trim()
    if (decision === 'changes_requested' && !cleanComment) {
      setError('Describe the requested changes.')
      return
    }
    setBusy(true)
    setError('')
    try {
      await modelingApi.decideApproval(projectId, approval.approval_id, {
        decision,
        payload_hash: approval.payload_hash,
        comment: cleanComment,
      })
      await onDecided()
    } catch {
      setError('Unable to record the approval decision.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-900 dark:bg-amber-950">
      <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Model plan approval</h2>
      <p className="mt-1 break-all text-xs text-gray-600 dark:text-gray-300">Plan artifact SHA-256: {approval.payload.artifact_sha256}</p>
      <p className="mt-1 break-all text-xs text-gray-600 dark:text-gray-300">Approval payload hash: {approval.payload_hash}</p>
      <p className="mt-3 text-sm text-gray-700 dark:text-gray-200">{plan.problem_summary}</p>
      <div className="mt-3 space-y-3">
        {plan.candidates.map((candidate) => (
          <article key={candidate.name} className="rounded border border-amber-200 bg-white p-3 dark:border-amber-900 dark:bg-gray-900">
            <h3 className="font-medium text-gray-900 dark:text-gray-100">{candidate.name}</h3>
            <p className="mt-1 text-xs text-gray-600 dark:text-gray-300">Algorithm: {candidate.algorithm}</p>
            <p className="mt-1 text-xs text-gray-600 dark:text-gray-300">Risks: {candidate.risks.join(', ') || 'None'}</p>
          </article>
        ))}
      </div>
      {error && <p role="alert" className="mt-3 text-sm text-red-700 dark:text-red-300">{error}</p>}
      <label className="mt-4 block text-xs font-medium text-gray-700 dark:text-gray-200">
        Approval comment
        <textarea aria-label="Approval comment" value={comment} onChange={(event) => setComment(event.target.value)} className="mt-1 block w-full rounded border border-gray-300 p-2 text-sm dark:border-gray-700 dark:bg-gray-950" />
      </label>
      <div className="mt-3 flex gap-2">
        <button type="button" disabled={busy} onClick={() => void decide('approved')} className="rounded bg-green-700 px-3 py-2 text-sm font-medium text-white disabled:bg-gray-400">{busy && <Loader2 className="mr-1 inline h-3 w-3 animate-spin" />}Approve plan</button>
        <button type="button" disabled={busy} onClick={() => void decide('changes_requested')} className="rounded border border-amber-500 px-3 py-2 text-sm font-medium text-amber-900 dark:text-amber-100">Request changes</button>
      </div>
    </section>
  )
}
