import { useState } from 'react'
import { Loader2, Upload } from 'lucide-react'
import { modelingApi } from '../services/api'

interface ModelingInputPanelProps {
  projectId: string
  disabled?: boolean
  onChanged: () => void | Promise<void>
}

export default function ModelingInputPanel({ projectId, disabled = false, onChanged }: ModelingInputPanelProps) {
  const [problem, setProblem] = useState<File | null>(null)
  const [data, setData] = useState<File | null>(null)
  const [busy, setBusy] = useState<'problem' | 'data' | null>(null)
  const [error, setError] = useState('')

  const upload = async (kind: 'problem' | 'data', file: File | null) => {
    if (!file) return
    setBusy(kind)
    setError('')
    try {
      await modelingApi.uploadInput(projectId, kind, file)
      await onChanged()
    } catch {
      setError(`Unable to upload ${kind} input.`)
    } finally {
      setBusy(null)
    }
  }

  return (
    <section className="rounded-lg border border-gray-200 p-4 dark:border-gray-800" aria-labelledby="modeling-inputs-title">
      <h2 id="modeling-inputs-title" className="text-sm font-semibold text-gray-900 dark:text-gray-100">Competition inputs</h2>
      <p className="mt-1 text-xs text-gray-500">Uploaded problem and CSV files become immutable raw inputs.</p>
      {error && <p role="alert" className="mt-3 text-sm text-red-700 dark:text-red-300">{error}</p>}
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <label className="text-sm text-gray-700 dark:text-gray-200">
          <span className="mb-1 block font-medium">Problem file</span>
          <input type="file" disabled={disabled} accept=".pdf,.md,.txt" onChange={(event) => setProblem(event.target.files?.[0] || null)} className="block w-full text-xs" />
          <button type="button" disabled={disabled || !problem || busy !== null} onClick={() => void upload('problem', problem)} className="mt-2 inline-flex items-center gap-1 rounded bg-blue-600 px-3 py-2 text-xs font-medium text-white disabled:bg-gray-300">
            {busy === 'problem' ? <Loader2 className="h-3 w-3 animate-spin" /> : <Upload className="h-3 w-3" />}Upload problem
          </button>
        </label>
        <label className="text-sm text-gray-700 dark:text-gray-200">
          <span className="mb-1 block font-medium">CSV data file</span>
          <input type="file" disabled={disabled} accept=".csv" onChange={(event) => setData(event.target.files?.[0] || null)} className="block w-full text-xs" />
          <button type="button" disabled={disabled || !data || busy !== null} onClick={() => void upload('data', data)} className="mt-2 inline-flex items-center gap-1 rounded bg-blue-600 px-3 py-2 text-xs font-medium text-white disabled:bg-gray-300">
            {busy === 'data' ? <Loader2 className="h-3 w-3 animate-spin" /> : <Upload className="h-3 w-3" />}Upload data
          </button>
        </label>
      </div>
    </section>
  )
}
