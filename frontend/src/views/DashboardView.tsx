import { useEffect, useMemo, useState } from 'react'
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  Loader2,
  MessageSquare,
  Plus,
  Settings,
} from 'lucide-react'
import { settingsApi, type SettingsStatus } from '../services/api'
import type { AppModule } from '../store/useStore'
import { useStore } from '../store/useStore'

interface DashboardViewProps {
  onOpenUpload: () => void
  onOpenSettings: () => void
  onModuleChange: (module: AppModule) => void
}

export default function DashboardView({
  onOpenUpload,
  onOpenSettings,
  onModuleChange,
}: DashboardViewProps) {
  const { documents, messages, selectedDocIds } = useStore()
  const [settingsStatus, setSettingsStatus] = useState<SettingsStatus | null>(null)
  const [isLoadingSettings, setIsLoadingSettings] = useState(false)

  useEffect(() => {
    let isMounted = true
    setIsLoadingSettings(true)

    settingsApi.getStatus()
      .then((status) => {
        if (isMounted) setSettingsStatus(status)
      })
      .catch((error) => {
        console.error('Failed to load settings status:', error)
      })
      .finally(() => {
        if (isMounted) setIsLoadingSettings(false)
      })

    return () => {
      isMounted = false
    }
  }, [])

  const completedCount = useMemo(
    () => documents.filter((doc) => doc.status === 'completed').length,
    [documents],
  )
  const processingCount = useMemo(
    () => documents.filter((doc) => doc.status === 'processing').length,
    [documents],
  )
  const recentDocuments = documents.slice(0, 5)

  return (
    <div className="h-full overflow-y-auto bg-gray-100 p-6 dark:bg-gray-950">
      <div className="mx-auto max-w-6xl space-y-6">
        <section className="grid gap-4 md:grid-cols-4">
          <MetricCard label="Sources" value={documents.length} detail={`${completedCount} ready`} />
          <MetricCard label="Selected" value={selectedDocIds.length} detail="active context" />
          <MetricCard label="Messages" value={messages.length} detail="current chat" />
          <MetricCard label="Processing" value={processingCount} detail="background jobs" />
        </section>

        <section className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
          <div className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-semibold text-gray-950 dark:text-gray-100">Recent sources</h2>
                <p className="text-xs text-gray-500 dark:text-gray-400">Latest files available to the workbench</p>
              </div>
              <button
                onClick={onOpenUpload}
                className="flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                <Plus className="h-4 w-4" />
                Add
              </button>
            </div>

            {recentDocuments.length === 0 ? (
              <EmptyPanel
                icon={<FileText className="h-6 w-6" />}
                title="No sources yet"
                description="Upload PDFs, documents, or text files to start a grounded workspace."
              />
            ) : (
              <div className="divide-y divide-gray-100 dark:divide-gray-800">
                {recentDocuments.map((doc) => (
                  <div key={doc.doc_id} className="flex items-center gap-3 py-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300">
                      <FileText className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-gray-950 dark:text-gray-100">{doc.filename}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{doc.total_chunks} chunks</p>
                    </div>
                    <StatusPill status={doc.status} />
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-sm font-semibold text-gray-950 dark:text-gray-100">Runtime</h2>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Backend model configuration</p>
                </div>
                <button
                  onClick={onOpenSettings}
                  className="flex h-9 w-9 items-center justify-center rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
                  aria-label="Open settings"
                  title="Open settings"
                >
                  <Settings className="h-4 w-4" />
                </button>
              </div>

              {isLoadingSettings ? (
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Loading runtime status
                </div>
              ) : settingsStatus ? (
                <div className="space-y-3">
                  <div>
                    <p className="text-xs uppercase text-gray-500 dark:text-gray-400">Provider</p>
                    <p className="truncate text-sm font-semibold text-gray-950 dark:text-gray-100">
                      {settingsStatus.provider} / {settingsStatus.model}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    {settingsStatus.api_key_configured ? (
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-amber-600" />
                    )}
                    <span className="text-gray-700 dark:text-gray-300">
                      API key {settingsStatus.api_key_configured ? 'configured' : 'missing'}
                    </span>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-gray-500">Runtime status unavailable.</p>
              )}
            </div>

            <div className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
              <h2 className="text-sm font-semibold text-gray-950 dark:text-gray-100">Quick actions</h2>
              <div className="mt-4 grid gap-2">
                <ActionButton
                  icon={<MessageSquare className="h-4 w-4" />}
                  label="Open workbench"
                  onClick={() => onModuleChange('workbench')}
                />
                <ActionButton
                  icon={<FileText className="h-4 w-4" />}
                  label="Manage sources"
                  onClick={() => onModuleChange('sources')}
                />
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

interface MetricCardProps {
  label: string
  value: number
  detail: string
}

function MetricCard({ label, value, detail }: MetricCardProps) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900">
      <p className="text-xs font-medium uppercase text-gray-500 dark:text-gray-400">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-gray-950 dark:text-gray-100">{value}</p>
      <p className="text-xs text-gray-500 dark:text-gray-400">{detail}</p>
    </div>
  )
}

interface EmptyPanelProps {
  icon: React.ReactNode
  title: string
  description: string
}

function EmptyPanel({ icon, title, description }: EmptyPanelProps) {
  return (
    <div className="flex min-h-52 items-center justify-center rounded-lg border border-dashed border-gray-300 p-6 text-center dark:border-gray-700">
      <div>
        <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-lg bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400">
          {icon}
        </div>
        <p className="mt-3 text-sm font-medium text-gray-800 dark:text-gray-200">{title}</p>
        <p className="mt-1 max-w-sm text-xs leading-relaxed text-gray-500 dark:text-gray-400">{description}</p>
      </div>
    </div>
  )
}

interface ActionButtonProps {
  icon: React.ReactNode
  label: string
  onClick: () => void
}

function ActionButton({ icon, label, onClick }: ActionButtonProps) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
    >
      {icon}
      {label}
    </button>
  )
}

function StatusPill({ status }: { status: string }) {
  const className =
    status === 'completed'
      ? 'bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300'
      : status === 'processing'
        ? 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300'
        : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'

  return (
    <span className={`rounded-md px-2 py-1 text-xs font-medium ${className}`}>
      {status}
    </span>
  )
}
