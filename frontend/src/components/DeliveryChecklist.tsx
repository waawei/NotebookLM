import { useEffect, useState } from 'react'
import { modelingApi } from '../services/api'

export default function DeliveryChecklist({ projectId, onChanged }: { projectId: string; onChanged: () => void | Promise<void> }) {
  const [check, setCheck] = useState<{ ok: boolean; issues: Array<{ code: string; message: string }> } | null>(null)
  const [busy, setBusy] = useState(false)
  useEffect(() => { if (typeof modelingApi.checkDeliverables === 'function') void modelingApi.checkDeliverables(projectId).then(setCheck) }, [projectId])
  const build = async () => { if (typeof modelingApi.buildDeliverables !== 'function' || typeof modelingApi.checkDeliverables !== 'function') return; setBusy(true); try { await modelingApi.buildDeliverables(projectId); await onChanged(); setCheck(await modelingApi.checkDeliverables(projectId)) } finally { setBusy(false) } }
  return <section className="rounded border border-gray-200 p-3 dark:border-gray-800"><h2 className="text-sm font-semibold">Delivery checklist</h2>{check && <ul className="mt-2 text-sm">{check.issues.map((issue) => <li key={issue.code}>{issue.code}: {issue.message}</li>)}</ul>}<button type="button" disabled={!check?.ok || busy} onClick={() => void build()} className="mt-3 rounded bg-blue-600 px-3 py-2 text-sm text-white disabled:bg-gray-400">Build deliverables</button></section>
}
