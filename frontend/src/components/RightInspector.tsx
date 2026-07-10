import { useEffect, useMemo, useState } from 'react'
import {
  AlertCircle,
  BookText,
  CheckCircle2,
  Loader2,
  Quote,
  Server,
} from 'lucide-react'
import { noteApi, settingsApi, type NoteItem, type SettingsStatus } from '../services/api'
import { t } from '../i18n'
import { useStore, type Citation } from '../store/useStore'
import ArtifactList from './ArtifactList'
import PreviewPane from './PreviewPane'
import TaskProgressCards from './TaskProgressCards'
import WorkspaceToolsPanel from './WorkspaceToolsPanel'

type RightPanelTab = 'workspace' | 'preview'

export default function RightInspector() {
  const { messages, previewTarget, language } = useStore()
  const [activePanelTab, setActivePanelTab] = useState<RightPanelTab>(() => previewTarget ? 'preview' : 'workspace')

  useEffect(() => {
    if (previewTarget) {
      setActivePanelTab('preview')
    }
  }, [previewTarget])

  const latestCitations = useMemo(() => {
    const latestAssistantWithCitations = [...messages]
      .reverse()
      .find((message) => message.role === 'assistant' && message.citations && message.citations.length > 0)

    return latestAssistantWithCitations?.citations || []
  }, [messages])

  return (
    <div data-testid="right-workspace-panel" className="flex h-full flex-col bg-[#f8f7f6] dark:bg-gray-950">
      <div className="border-b border-[#e2e1de] px-4 py-3 dark:border-gray-800">
        <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">{t(language, 'right.workspace')}</h2>
        <p className="text-xs text-gray-500 dark:text-gray-400">{t(language, 'right.subtitle')}</p>
      </div>

      <div className="grid grid-cols-2 border-b border-[#e2e1de] p-2 dark:border-gray-800">
        {[
          { key: 'workspace' as const, label: t(language, 'right.workspace') },
          { key: 'preview' as const, label: t(language, 'right.preview') },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActivePanelTab(tab.key)}
            className={`rounded-md px-2 py-1.5 text-xs font-medium transition-colors ${
              activePanelTab === tab.key
                ? 'bg-blue-50 text-blue-700 shadow-sm ring-1 ring-blue-100 dark:bg-blue-950 dark:text-blue-200 dark:ring-blue-900'
                : 'text-gray-500 hover:bg-white hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activePanelTab === 'workspace' ? (
        <div data-testid="workspace-tab-panel" className="min-h-0 flex-1 overflow-y-auto">
          <div className="space-y-5 p-4">
            <WorkspaceToolsPanel />
            <TaskProgressCards />
            <ArtifactList />
            <section aria-labelledby="workspace-evidence-heading" className="space-y-2">
              <h3 id="workspace-evidence-heading" className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Evidence
              </h3>
              <CitationsPanel citations={latestCitations} />
            </section>
            <section aria-labelledby="workspace-notes-heading" className="space-y-2">
              <h3 id="workspace-notes-heading" className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Notes
              </h3>
              <NotesPanel />
            </section>
            <section aria-labelledby="workspace-runtime-heading" className="space-y-2">
              <h3 id="workspace-runtime-heading" className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Runtime
              </h3>
              <RuntimePanel />
            </section>
          </div>
        </div>
      ) : (
        <div data-testid="preview-tab-panel" className="min-h-0 flex-1 overflow-y-auto p-4">
          <PreviewPane />
        </div>
      )}
    </div>
  )
}

function CitationsPanel({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) {
    return (
      <EmptyState
        icon={<Quote className="h-5 w-5" />}
        title="No citations yet"
        description="Ask a question against selected sources. Retrieved evidence will appear here."
      />
    )
  }

  return (
    <div className="space-y-3">
      {citations.map((citation, index) => (
        <article
          key={`${citation.doc_id}-${citation.chunk_id}-${index}`}
          data-testid="workspace-citation-card"
          className="rounded-lg border border-[#e2e1de] bg-white p-3 shadow-sm dark:border-gray-800 dark:bg-gray-900"
        >
          <div className="mb-2 flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-gray-950 dark:text-gray-100">
                [{citation.number}] {citation.doc_name}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {citation.page
                  ? `Page ${citation.page}`
                  : citation.section
                    ? `Section ${citation.section}`
                    : 'Source section'} · {Math.round(citation.relevance_score * 100)}%
              </p>
            </div>
            <span className="rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 dark:bg-blue-950 dark:text-blue-300">
              #{citation.number}
            </span>
          </div>
          <p className="line-clamp-6 text-xs leading-relaxed text-gray-600 dark:text-gray-300">
            {citation.content}
          </p>
        </article>
      ))}
    </div>
  )
}

function NotesPanel() {
  const [notes, setNotes] = useState<NoteItem[]>([])
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    let isMounted = true
    setIsLoading(true)

    noteApi.list()
      .then((data) => {
        if (isMounted) setNotes(data.notes.slice(0, 6))
      })
      .catch((error) => {
        console.error('Failed to load notes for inspector:', error)
      })
      .finally(() => {
        if (isMounted) setIsLoading(false)
      })

    return () => {
      isMounted = false
    }
  }, [])

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading notes
      </div>
    )
  }

  if (notes.length === 0) {
    return (
      <EmptyState
        icon={<BookText className="h-5 w-5" />}
        title="No notes saved"
        description="Use Save as Note on assistant answers to capture reusable material."
      />
    )
  }

  return (
    <div className="space-y-2">
      {notes.map((note) => (
        <article
          key={note.note_id}
          className="rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-800 dark:bg-gray-900"
        >
          <p className="truncate text-sm font-semibold text-gray-950 dark:text-gray-100">{note.title}</p>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Updated {new Date(note.updated_at).toLocaleDateString()}
          </p>
        </article>
      ))}
    </div>
  )
}

function RuntimePanel() {
  const [status, setStatus] = useState<SettingsStatus | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    let isMounted = true
    setIsLoading(true)

    settingsApi.getStatus()
      .then((data) => {
        if (isMounted) setStatus(data)
      })
      .catch((error) => {
        console.error('Failed to load runtime status for inspector:', error)
      })
      .finally(() => {
        if (isMounted) setIsLoading(false)
      })

    return () => {
      isMounted = false
    }
  }, [])

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading runtime
      </div>
    )
  }

  if (!status) {
    return (
      <EmptyState
        icon={<AlertCircle className="h-5 w-5" />}
        title="Runtime unavailable"
        description="The backend settings endpoint could not be reached."
      />
    )
  }

  return (
    <div className="space-y-3">
      <RuntimeRow label="Provider" value={status.provider} icon={<Server className="h-4 w-4" />} />
      <RuntimeRow label="Model" value={status.model} />
      <RuntimeRow
        label="API Key"
        value={status.api_key_configured ? 'Configured' : 'Missing'}
        icon={status.api_key_configured ? <CheckCircle2 className="h-4 w-4 text-green-600" /> : <AlertCircle className="h-4 w-4 text-amber-600" />}
      />
      <RuntimeRow label="Base URL" value={status.base_url_configured ? 'Custom configured' : 'Default provider URL'} />
      <RuntimeRow label="Embedding" value={`${status.embedding_model} (${status.embedding_device})`} />
      {status.warnings.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 dark:border-amber-900 dark:bg-amber-950">
          <p className="text-xs font-semibold text-amber-900 dark:text-amber-100">Warnings</p>
          <ul className="mt-2 space-y-1">
            {status.warnings.map((warning) => (
              <li key={warning} className="text-xs leading-relaxed text-amber-800 dark:text-amber-200">
                {warning}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

interface RuntimeRowProps {
  label: string
  value: string
  icon?: React.ReactNode
}

function RuntimeRow({ label, value, icon }: RuntimeRowProps) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-800 dark:bg-gray-900">
      <div className="mb-1 flex items-center gap-2 text-gray-500 dark:text-gray-400">
        {icon}
        <p className="text-xs font-semibold uppercase">{label}</p>
      </div>
      <p className="break-all text-sm font-medium text-gray-950 dark:text-gray-100">{value}</p>
    </div>
  )
}

interface EmptyStateProps {
  icon: React.ReactNode
  title: string
  description: string
}

function EmptyState({ icon, title, description }: EmptyStateProps) {
  return (
    <div className="flex h-full items-center justify-center text-center">
      <div>
        <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-lg bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400">
          {icon}
        </div>
        <p className="mt-3 text-sm font-medium text-gray-800 dark:text-gray-200">{title}</p>
        <p className="mt-1 text-xs leading-relaxed text-gray-500 dark:text-gray-400">{description}</p>
      </div>
    </div>
  )
}
