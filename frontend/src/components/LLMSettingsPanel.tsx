import { useEffect, useState } from 'react'
import { AlertCircle, CheckCircle2, Eye, EyeOff, RefreshCw, Server, ShieldCheck } from 'lucide-react'
import { settingsApi, type SettingsConfigUpdate, type SettingsEndpointMode, type SettingsStatus, type SettingsTestResult } from '../services/api'

const PROVIDER_PRESETS: Record<string, { model: string; baseUrl: string; endpointMode: SettingsEndpointMode; keyPlaceholder: string }> = {
  ollama: {
    model: 'qwen3:8b',
    baseUrl: 'http://localhost:11434',
    endpointMode: 'auto',
    keyPlaceholder: 'Optional for local Ollama',
  },
  deepseek: {
    model: 'deepseek-v4-flash',
    baseUrl: 'https://api.deepseek.com',
    endpointMode: 'exact',
    keyPlaceholder: 'Required by DeepSeek',
  },
}

export default function LLMSettingsPanel() {
  const [status, setStatus] = useState<SettingsStatus | null>(null)
  const [provider, setProvider] = useState('openai')
  const [model, setModel] = useState('')
  const [baseUrl, setBaseUrl] = useState('')
  const [baseUrlTouched, setBaseUrlTouched] = useState(false)
  const [endpointMode, setEndpointMode] = useState<SettingsEndpointMode>('auto')
  const [apiKey, setApiKey] = useState('')
  const [showApiKey, setShowApiKey] = useState(false)
  const [models, setModels] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isClearing, setIsClearing] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [isLoadingModels, setIsLoadingModels] = useState(false)
  const [message, setMessage] = useState<SettingsTestResult | null>(null)

  const applyStatus = (nextStatus: SettingsStatus) => {
    setStatus(nextStatus)
    setProvider(nextStatus.provider)
    setModel(nextStatus.model)
    setEndpointMode(nextStatus.endpoint_mode || 'auto')
    setBaseUrl('')
    setBaseUrlTouched(false)
  }

  const loadStatus = async () => {
    setIsLoading(true)
    setMessage(null)
    try {
      applyStatus(await settingsApi.getStatus())
    } catch {
      setMessage({ ok: false, message: 'Unable to load LLM configuration status.' })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadStatus()
  }, [])

  const changeProvider = (nextProvider: string) => {
    setProvider(nextProvider)
    const preset = PROVIDER_PRESETS[nextProvider]
    if (!preset) return
    setModel(preset.model)
    setBaseUrl(preset.baseUrl)
    setBaseUrlTouched(true)
    setEndpointMode(preset.endpointMode)
    setApiKey('')
    setShowApiKey(false)
  }

  const saveConfiguration = async () => {
    setIsSaving(true)
    setMessage(null)
    const payload: SettingsConfigUpdate = { provider, model, endpoint_mode: endpointMode }
    if (baseUrlTouched) payload.base_url = baseUrl.trim()
    if (apiKey) payload.api_key = apiKey

    try {
      applyStatus(await settingsApi.save(payload))
      setMessage({ ok: true, message: 'Local LLM configuration saved.' })
    } catch {
      setMessage({ ok: false, message: 'Unable to save LLM configuration. Check the values and try again.' })
    } finally {
      setApiKey('')
      setShowApiKey(false)
      setIsSaving(false)
    }
  }

  const clearConfiguration = async () => {
    setIsClearing(true)
    setMessage(null)
    try {
      applyStatus(await settingsApi.clear())
      setApiKey('')
      setShowApiKey(false)
      setMessage({ ok: true, message: 'Local LLM configuration cleared. Environment defaults are active.' })
    } catch {
      setMessage({ ok: false, message: 'Unable to clear local LLM configuration.' })
    } finally {
      setIsClearing(false)
    }
  }

  const testConnection = async () => {
    setIsTesting(true)
    setMessage(null)
    const payload: SettingsConfigUpdate = { provider, model, endpoint_mode: endpointMode }
    if (baseUrlTouched) payload.base_url = baseUrl.trim()
    if (apiKey) payload.api_key = apiKey
    try {
      setMessage(await settingsApi.testLlm(payload))
    } catch {
      setMessage({ ok: false, message: 'Unable to test the LLM connection.' })
    } finally {
      setApiKey('')
      setShowApiKey(false)
      setIsTesting(false)
    }
  }

  const loadModels = async () => {
    setIsLoadingModels(true)
    setMessage(null)
    const payload = { provider, endpoint_mode: endpointMode } as Parameters<typeof settingsApi.listModels>[0]
    if (baseUrlTouched) payload.base_url = baseUrl.trim()
    if (apiKey) payload.api_key = apiKey

    try {
      const result = await settingsApi.listModels(payload)
      setModels(result.models)
      setMessage({ ok: true, message: 'Available models updated. You can select one or enter a model manually.' })
    } catch {
      setMessage({ ok: false, message: 'Unable to load available models. Check the provider, endpoint, and API key.' })
    } finally {
      setApiKey('')
      setShowApiKey(false)
      setIsLoadingModels(false)
    }
  }

  return (
    <div className="space-y-5">
      <section className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300">
            <Server className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-950 dark:text-gray-100">Runtime settings</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">Configure a backend-local model connection. API keys are write-only and never displayed.</p>
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h3 className="font-semibold text-gray-950 dark:text-gray-100">LLM connection</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Saved values take precedence over compatible backend environment defaults.</p>
          </div>
          <button onClick={() => void loadStatus()} disabled={isLoading} className="rounded-lg border border-gray-300 p-2 text-gray-700 hover:bg-gray-50 disabled:opacity-60 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800" aria-label="Refresh settings">
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">Provider
            <select value={provider} onChange={(event) => changeProvider(event.target.value)} className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-950 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100">
              <option value="openai">OpenAI</option>
              <option value="dashscope">DashScope</option>
              <option value="openai_compatible">OpenAI compatible</option>
              <option value="ollama">Ollama</option>
              <option value="deepseek">DeepSeek</option>
            </select>
          </label>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">Model
            <input aria-label="Model" list="available-models" value={model} onChange={(event) => setModel(event.target.value)} required className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-950 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100" />
            <datalist id="available-models">{models.map((availableModel) => <option key={availableModel} value={availableModel}>{availableModel}</option>)}</datalist>
          </label>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">Endpoint format
            <select aria-label="Endpoint format" value={endpointMode} onChange={(event) => setEndpointMode(event.target.value as SettingsEndpointMode)} className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-950 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100">
              <option value="auto">Automatic /v1</option>
              <option value="exact">Exact API base</option>
            </select>
          </label>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">Base URL
            <input aria-label="Base URL" value={baseUrl} onChange={(event) => { setBaseUrl(event.target.value); setBaseUrlTouched(true) }} placeholder={status?.base_url_configured ? 'Custom URL configured; enter a replacement to change it' : 'Optional provider endpoint'} className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-950 placeholder:text-gray-400 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100" />
            <span className="mt-1 block text-xs font-normal text-gray-500 dark:text-gray-400">Automatic accepts the API root or /v1 (with or without a trailing slash). Exact preserves a documented custom API base. Do not enter /models or /chat/completions.</span>
          </label>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">API key
            <span className="mt-1 flex gap-2"><input aria-label="API key" type={showApiKey ? 'text' : 'password'} autoComplete="off" value={apiKey} onChange={(event) => setApiKey(event.target.value)} placeholder={status?.api_key_configured ? 'Configured; enter a replacement only' : PROVIDER_PRESETS[provider]?.keyPlaceholder || 'Required by most providers'} className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-950 placeholder:text-gray-400 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100" /><button type="button" aria-label={showApiKey ? 'Hide API key' : 'Show API key'} onClick={() => setShowApiKey((visible) => !visible)} className="rounded-lg border border-gray-300 px-3 text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800">{showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}</button></span>
          </label>
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          <button onClick={() => void saveConfiguration()} disabled={isSaving || !model.trim()} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60">{isSaving ? 'Saving…' : 'Save configuration'}</button>
          <button onClick={() => void testConnection()} disabled={isTesting} className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-60 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800">{isTesting ? 'Testing…' : 'Test connection'}</button>
          <button onClick={() => void loadModels()} disabled={isLoadingModels} className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-60 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800">{isLoadingModels ? 'Loading models…' : 'Load available models'}</button>
          <button onClick={() => void clearConfiguration()} disabled={isClearing} className="rounded-lg border border-red-200 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-60 dark:border-red-900 dark:text-red-300 dark:hover:bg-red-950">{isClearing ? 'Clearing…' : 'Clear local configuration'}</button>
        </div>

        {message && <Feedback message={message} />}
      </section>

      {status && <>
        <section className="grid gap-3 md:grid-cols-2">
          <StatusCard label="Provider" value={status.provider} icon={<Server className="h-4 w-4" />} />
          <StatusCard label="Model" value={status.model} />
          <StatusCard label="API key" value={status.api_key_configured ? 'Configured' : 'Missing'} tone={status.api_key_configured ? 'success' : 'warning'} icon={<ShieldCheck className="h-4 w-4" />} />
          <StatusCard label="Base URL" value={status.base_url_configured ? 'Custom configured' : 'Default provider URL'} />
        </section>
        {status.warnings.length > 0 && <section className="rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-900 dark:bg-amber-950"><div className="flex gap-2"><AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-300" /><div><p className="text-sm font-semibold text-amber-900 dark:text-amber-100">Configuration warnings</p><ul className="mt-1 space-y-1 text-sm text-amber-800 dark:text-amber-200">{status.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul></div></div></section>}
      </>}
    </div>
  )
}

function Feedback({ message }: { message: SettingsTestResult }) {
  const isSuccess = message.ok
  return <div className={`mt-4 flex gap-2 rounded-lg border p-3 text-sm ${isSuccess ? 'border-green-200 bg-green-50 text-green-800 dark:border-green-900 dark:bg-green-950 dark:text-green-200' : 'border-red-200 bg-red-50 text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200'}`}>
    {isSuccess ? <CheckCircle2 className="h-5 w-5 shrink-0" /> : <AlertCircle className="h-5 w-5 shrink-0" />}
    <div className="min-w-0 flex-1"><p>{message.message}</p>{!isSuccess && message.diagnostic && <details className="mt-3 border-t border-current/20 pt-3"><summary className="cursor-pointer font-medium">Connection details</summary><dl className="mt-3 grid gap-2 text-xs"><DiagnosticRow label="Request phase" value={message.diagnostic.phase} />{message.diagnostic.status_code !== null && <DiagnosticRow label="HTTP status" value={String(message.diagnostic.status_code)} />}<DiagnosticRow label="Category" value={message.diagnostic.category} /><DiagnosticRow label="Summary" value={message.diagnostic.summary} /></dl></details>}</div>
  </div>
}

function DiagnosticRow({ label, value }: { label: string; value: string }) {
  return <div className="grid gap-1 sm:grid-cols-[8rem_1fr]"><dt className="font-semibold">{label}</dt><dd className="break-words">{value}</dd></div>
}

function StatusCard({ label, value, tone = 'default', icon }: { label: string; value: string; tone?: 'default' | 'success' | 'warning'; icon?: React.ReactNode }) {
  const toneClass = tone === 'success' ? 'border-green-200 bg-green-50 text-green-800 dark:border-green-900 dark:bg-green-950 dark:text-green-200' : tone === 'warning' ? 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200' : 'border-gray-200 bg-white text-gray-950 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-100'
  return <div className={`rounded-lg border p-4 ${toneClass}`}><div className="mb-1 flex items-center gap-2 text-gray-500 dark:text-gray-400">{icon}<p className="text-xs font-semibold uppercase">{label}</p></div><p className="break-all text-sm font-semibold">{value}</p></div>
}
