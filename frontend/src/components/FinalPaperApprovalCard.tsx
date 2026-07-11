import { useState } from 'react'
import { modelingApi, type ApprovalRequest, type PaperReview } from '../services/api'

export default function FinalPaperApprovalCard({ projectId, review, approval, onChanged }: { projectId: string; review?: PaperReview; approval?: ApprovalRequest; onChanged: () => void | Promise<void> }) {
  const [busy, setBusy] = useState(false)
  const blocked = !review || review.status !== 'passed'
  const request = async () => { setBusy(true); try { await modelingApi.requestFinalApproval(projectId); await onChanged() } finally { setBusy(false) } }
  const approve = async () => { if (!approval) return; setBusy(true); try { await modelingApi.decideApproval(projectId, approval.approval_id, { decision: 'approved', payload_hash: approval.payload_hash, comment: '' }); await onChanged() } finally { setBusy(false) } }
  return <section className="rounded border border-amber-200 bg-amber-50 p-3 dark:border-amber-900 dark:bg-amber-950"><h2 className="text-sm font-semibold">Final paper approval</h2><button type="button" disabled={blocked || busy} onClick={() => void (approval ? approve() : request())} className="mt-3 rounded bg-green-700 px-3 py-2 text-sm text-white disabled:bg-gray-400">{approval ? 'Approve final paper' : 'Request final approval'}</button></section>
}
