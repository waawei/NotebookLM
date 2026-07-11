import { type PaperClaim, type PaperReview } from '../services/api'

export default function ReviewIssuesPanel({ review, claims }: { review?: PaperReview; claims: PaperClaim[] }) {
  return <aside className="space-y-4" aria-label="Paper evidence and review">
    <section className="rounded border border-gray-200 p-3 dark:border-gray-800"><h2 className="text-sm font-semibold">Claim provenance</h2><ul className="mt-2 space-y-2 text-xs">{claims.map((claim) => <li key={`${claim.placeholder}-${claim.artifact_id}`}><code className="break-all">{claim.placeholder}</code><p className="text-gray-500">{claim.experiment_id} · {claim.artifact_id}</p></li>)}{claims.length === 0 && <li className="text-gray-500">No resolved claims.</li>}</ul></section>
    <section className="rounded border border-gray-200 p-3 dark:border-gray-800"><h2 className="text-sm font-semibold">Review issues</h2>{review ? <ul className="mt-2 space-y-2 text-xs">{review.issues.map((issue) => <li key={`${issue.code}-${issue.location}`} className={issue.severity === 'blocking' ? 'text-red-700 dark:text-red-300' : 'text-gray-600 dark:text-gray-300'}>{issue.message}</li>)}{review.issues.length === 0 && <li className="text-green-700 dark:text-green-300">Review passed.</li>}</ul> : <p className="mt-2 text-xs text-gray-500">No review run.</p>}</section>
  </aside>
}
