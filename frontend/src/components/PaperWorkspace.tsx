import { useEffect, useState } from 'react'
import { modelingApi, type ApprovalRequest, type PaperClaim, type PaperReview } from '../services/api'
import FinalPaperApprovalCard from './FinalPaperApprovalCard'
import ReviewIssuesPanel from './ReviewIssuesPanel'

export default function PaperWorkspace({ projectId, markdown, latex, approval, onChanged }: { projectId: string; markdown: string; latex: string; approval?: ApprovalRequest; onChanged: () => void | Promise<void> }) {
  const [draft, setDraft] = useState(markdown)
  const [rendered, setRendered] = useState('')
  const [claims, setClaims] = useState<PaperClaim[]>([])
  const [review, setReview] = useState<PaperReview>()
  const [busy, setBusy] = useState(false)
  const [view, setView] = useState<'markdown' | 'latex' | 'pdf'>('markdown')
  useEffect(() => setDraft(markdown), [markdown])
  const action = async (kind: 'save' | 'review' | 'compile') => { setBusy(true); try { if (kind === 'save') await modelingApi.savePaperMarkdown(projectId, draft); if (kind === 'review') { const output = await modelingApi.renderPaper(projectId); setRendered(output.rendered); setClaims(output.claims); setReview(await modelingApi.reviewPaper(projectId)) } if (kind === 'compile') { await modelingApi.compilePaper(projectId); setView('pdf') } await onChanged() } finally { setBusy(false) } }
  return <section className="grid gap-4 xl:grid-cols-[minmax(0,1.3fr)_minmax(260px,.7fr)]" aria-label="Paper workspace"><div className="min-w-0 space-y-3"><div className="flex flex-wrap gap-2"><button type="button" onClick={() => void action('save')} disabled={busy} className="rounded bg-blue-600 px-3 py-2 text-sm text-white">Save</button><button type="button" onClick={() => void action('review')} disabled={busy} className="rounded border px-3 py-2 text-sm">Review</button><button type="button" onClick={() => void action('compile')} disabled={busy || review?.status !== 'passed'} className="rounded border px-3 py-2 text-sm">Compile</button></div><textarea aria-label="Paper markdown" value={draft} onChange={(event) => setDraft(event.target.value)} className="min-h-[280px] w-full rounded border border-gray-200 p-3 font-mono text-sm dark:border-gray-800 dark:bg-gray-950" /><div className="flex gap-2 text-xs"><button type="button" onClick={() => setView('markdown')}>Markdown</button><button type="button" onClick={() => setView('latex')}>LaTeX</button><button type="button" onClick={() => setView('pdf')}>PDF</button></div>{view === 'markdown' && <pre className="max-h-52 overflow-auto whitespace-pre-wrap rounded border p-3 text-xs">{rendered || draft}</pre>}{view === 'latex' && <pre className="max-h-52 overflow-auto whitespace-pre-wrap rounded border p-3 text-xs">{latex}</pre>}{view === 'pdf' && <iframe title="Compiled paper PDF" src={modelingApi.paperPdfUrl(projectId)} className="h-80 w-full rounded border" />}</div><div className="space-y-4"><ReviewIssuesPanel review={review} claims={claims} /><FinalPaperApprovalCard projectId={projectId} review={review} approval={approval} onChanged={onChanged} /></div></section>
}
