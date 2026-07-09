import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import {
  AlertCircle,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Server,
  Settings,
  ShieldCheck,
  X,
} from 'lucide-react'
import { SettingsStatus, SettingsTestResult, settingsApi } from '../services/api'

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [status, setStatus] = useState<SettingsStatus | null>(null)
  const [testResult, setTestResult] = useState<SettingsTestResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isOpen) {
      loadStatus()
    }
  }, [isOpen])

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

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-3xl max-h-[86vh] bg-white dark:bg-gray-900 rounded-2xl shadow-2xl overflow-hidden border border-gray-200 dark:border-gray-800">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-50 dark:bg-blue-950 rounded-lg">
              <Settings className="w-5 h-5 text-blue-600 dark:text-blue-300" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">Settings</h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">Read-only runtime configuration from backend .env</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            aria-label="Close settings"
          >
            <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(86vh-73px)]">
          {isLoading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
            </div>
          ) : error ? (
            <div className="p-4 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-900 rounded-xl flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-300 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
            </div>
          ) : status ? (
            <div className="space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <StatusRow label="Provider" value={status.provider} icon={<Server className="w-4 h-4" />} />
                <StatusRow label="Model" value={status.model} />
                <StatusRow
                  label="API Key"
                  value={status.api_key_configured ? 'Configured' : 'Missing'}
                  tone={status.api_key_configured ? 'success' : 'warning'}
                  icon={<ShieldCheck className="w-4 h-4" />}
                />
                <StatusRow
                  label="Base URL"
                  value={status.base_url_configured ? 'Custom configured' : 'Default provider URL'}
                />
                <StatusRow label="Temperature" value={String(status.temperature)} />
                <StatusRow label="Max Tokens" value={String(status.max_tokens)} />
                <StatusRow label="Top K" value={String(status.top_k)} />
                <StatusRow label="Embedding Device" value={status.embedding_device} />
              </div>

              <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-2">Embedding Model</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100 break-all">{status.embedding_model}</p>
              </div>

              {status.warnings.length > 0 && (
                <div className="p-4 bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-900 rounded-xl">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-300" />
                    <p className="text-sm font-semibold text-amber-900 dark:text-amber-100">Configuration warnings</p>
                  </div>
                  <ul className="space-y-1">
                    {status.warnings.map((warning) => (
                      <li key={warning} className="text-sm text-amber-800 dark:text-amber-200">
                        {warning}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <button
                  onClick={loadStatus}
                  className="flex items-center justify-center gap-2 px-4 py-2.5 border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors font-medium"
                >
                  <RefreshCw className="w-4 h-4" />
                  Refresh
                </button>
                <button
                  onClick={testConnection}
                  disabled={isTesting}
                  className="flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  {isTesting ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                  Test LLM
                </button>
              </div>

              {testResult && (
                <div
                  className={`p-4 rounded-xl border flex items-start gap-3 ${
                    testResult.ok
                      ? 'bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-900'
                      : 'bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-900'
                  }`}
                >
                  {testResult.ok ? (
                    <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-300 flex-shrink-0 mt-0.5" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-300 flex-shrink-0 mt-0.5" />
                  )}
                  <p className={`text-sm ${testResult.ok ? 'text-green-800 dark:text-green-200' : 'text-red-800 dark:text-red-200'}`}>
                    {testResult.message}
                  </p>
                </div>
              )}

              <p className="text-xs text-gray-500 dark:text-gray-400">
                To change provider, model, base URL, or API key, edit backend `.env` and restart the backend.
              </p>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}

interface StatusRowProps {
  label: string
  value: string
  tone?: 'default' | 'success' | 'warning'
  icon?: ReactNode
}

function StatusRow({ label, value, tone = 'default', icon }: StatusRowProps) {
  const toneClass =
    tone === 'success'
      ? 'text-green-700 dark:text-green-300 bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-900'
      : tone === 'warning'
        ? 'text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950 border-amber-200 dark:border-amber-900'
        : 'text-gray-900 dark:text-gray-100 bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700'

  return (
    <div className={`p-4 rounded-xl border ${toneClass}`}>
      <div className="flex items-center gap-2 mb-1 text-gray-500 dark:text-gray-400">
        {icon}
        <p className="text-xs font-semibold uppercase tracking-wider">{label}</p>
      </div>
      <p className="text-sm font-semibold break-all">{value}</p>
    </div>
  )
}
