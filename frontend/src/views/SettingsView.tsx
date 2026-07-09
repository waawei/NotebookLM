import { useEffect, useState } from 'react'
import {
  AlertCircle,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Server,
  ShieldCheck,
} from 'lucide-react'
import { settingsApi, type SettingsStatus, type SettingsTestResult } from '../services/api'

export default function SettingsView() {
  const [status, setStatus] = useState<SettingsStatus | null>(null)
  const [testResult, setTestResult] = useState<SettingsTestResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    loadStatus()
  }, [])

  const loadStatus = async () => {
    setIsLoading(true)
    setError('')
    setTestResult(null)

    try {
      const data = await settingsApi.getStatus()
      setStatus(data)
    } catch (err) {
      console.error('Failed to load settings status:', err)
      setError('Unable to load backend settings status.')
    } finally {
      setIsLoading(false)
    }
  }

  const testConnection = async () => {
    setIsTesting(true)
    setTestResult(null)

    try {
      const result = await settingsApi.testLlm()
      setTestResult(result)
    } catch (err) {
      console.error('Failed to test LLM connection:', err)
      setTestResult({
        ok: false,
        message: 'Unable to reach backend test endpoint.',
      })
    } finally {
      setIsTesting(false)
    }
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-100 p-6 dark:bg-gray-950">
      <div className="mx-auto max-w-5xl space-y-5">
        <section className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300">
              <Server className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-950 dark:text-gray-100">Runtime settings</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Read-only configuration loaded from backend .env. Secrets are never shown here.
              </p>
            </div>
          </div>
        </section>

        {isLoading ? (
          <div className="flex items-center justify-center gap-2 rounded-lg border border-gray-200 bg-white py-16 text-sm text-gray-500 dark:border-gray-800 dark:bg-gray-900">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading settings
          </div>
        ) : error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950">
            <div className="flex items-start gap-2">
              <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-600 dark:text-red-300" />
              <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
            </div>
          </div>
        ) : status ? (
          <>
            <section className="grid gap-3 md:grid-cols-2">
              <StatusCard label="Provider" value={status.provider} icon={<Server className="h-4 w-4" />} />
              <StatusCard label="Model" value={status.model} />
              <StatusCard
                label="API Key"
                value={status.api_key_configured ? 'Configured' : 'Missing'}
                tone={status.api_key_configured ? 'success' : 'warning'}
                icon={<ShieldCheck className="h-4 w-4" />}
              />
              <StatusCard
                label="Base URL"
                value={status.base_url_configured ? 'Custom configured' : 'Default provider URL'}
              />
              <StatusCard label="Temperature" value={String(status.temperature)} />
              <StatusCard label="Max Tokens" value={String(status.max_tokens)} />
              <StatusCard label="Top K" value={String(status.top_k)} />
              <StatusCard label="Embedding Device" value={status.embedding_device} />
            </section>

            <section className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
              <p className="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Embedding Model</p>
              <p className="mt-2 break-all text-sm font-medium text-gray-950 dark:text-gray-100">{status.embedding_model}</p>
            </section>

            {status.warnings.length > 0 && (
              <section className="rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-900 dark:bg-amber-950">
                <div className="mb-2 flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-300" />
                  <p className="text-sm font-semibold text-amber-900 dark:text-amber-100">Configuration warnings</p>
                </div>
                <ul className="space-y-1">
                  {status.warnings.map((warning) => (
                    <li key={warning} className="text-sm text-amber-800 dark:text-amber-200">
                      {warning}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            <section className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
              <div className="flex flex-col gap-3 sm:flex-row">
                <button
                  onClick={loadStatus}
                  className="flex items-center justify-center gap-2 rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
                >
                  <RefreshCw className="h-4 w-4" />
                  Refresh
                </button>
                <button
                  onClick={testConnection}
                  disabled={isTesting}
                  className="flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isTesting ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                  Test LLM
                </button>
              </div>

              {testResult && (
                <div
                  className={`mt-4 rounded-lg border p-4 ${
                    testResult.ok
                      ? 'border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950'
                      : 'border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {testResult.ok ? (
                      <CheckCircle2 className="mt-0.5 h-5 w-5 flex-shrink-0 text-green-600 dark:text-green-300" />
                    ) : (
                      <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-600 dark:text-red-300" />
                    )}
                    <p className={`text-sm ${testResult.ok ? 'text-green-800 dark:text-green-200' : 'text-red-800 dark:text-red-200'}`}>
                      {testResult.message}
                    </p>
                  </div>
                </div>
              )}

              <p className="mt-4 text-xs text-gray-500 dark:text-gray-400">
                To change provider, model, base URL, or API key, edit backend `.env` and restart the backend.
              </p>
            </section>
          </>
        ) : null}
      </div>
    </div>
  )
}

interface StatusCardProps {
  label: string
  value: string
  tone?: 'default' | 'success' | 'warning'
  icon?: React.ReactNode
}

function StatusCard({ label, value, tone = 'default', icon }: StatusCardProps) {
  const toneClass =
    tone === 'success'
      ? 'border-green-200 bg-green-50 text-green-800 dark:border-green-900 dark:bg-green-950 dark:text-green-200'
      : tone === 'warning'
        ? 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200'
        : 'border-gray-200 bg-white text-gray-950 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-100'

  return (
    <div className={`rounded-lg border p-4 ${toneClass}`}>
      <div className="mb-1 flex items-center gap-2 text-gray-500 dark:text-gray-400">
        {icon}
        <p className="text-xs font-semibold uppercase">{label}</p>
      </div>
      <p className="break-all text-sm font-semibold">{value}</p>
    </div>
  )
}
