import { useEffect, useState } from 'react'
import { Loader2, RotateCcw, Trash2 } from 'lucide-react'
import { chatApi, wikiApi, type ConversationSummary, type WikiPage } from '../services/api'
import { useStore, type Message, type WorkbenchLeftTab } from '../store/useStore'
import Sidebar from './Sidebar'

interface WorkbenchContextPanelProps {
  isCollapsed: boolean
  onToggle: () => void
  onUploadClick: () => void
}

const tabOptions: Array<{ key: WorkbenchLeftTab; label: string; shortLabel?: string }> = [
  { key: 'conversations', label: 'Conversations' },
  { key: 'sources', label: 'Sources' },
  { key: 'knowledge_base', label: 'Knowledge Base', shortLabel: 'KB' },
]

export default function WorkbenchContextPanel({ isCollapsed, onToggle, onUploadClick }: WorkbenchContextPanelProps) {
  const { workbenchLeftTab, setWorkbenchLeftTab } = useStore()

  if (isCollapsed) {
    return <Sidebar isCollapsed={isCollapsed} onToggle={onToggle} onUploadClick={onUploadClick} />
  }

  return (
    <div data-testid="workbench-context-panel" className="flex h-full w-72 flex-col border-r border-[#dddcd9] bg-[#f1f0ef] dark:border-gray-800 dark:bg-gray-900">
      <div className="border-b border-[#dddcd9] bg-[#f8f7f6] p-3 dark:border-gray-800 dark:bg-gray-900">
        <div className="grid grid-cols-3 gap-1 rounded-lg border border-[#e2e1de] bg-[#ebeae8] p-1 dark:border-gray-800 dark:bg-gray-950">
          {tabOptions.map((tab) => (
            <button
              key={tab.key}
              type="button"
              aria-label={tab.label}
              onClick={() => setWorkbenchLeftTab(tab.key)}
              className={`h-8 rounded-md px-2 text-[11px] font-semibold transition-colors ${
                workbenchLeftTab === tab.key
                  ? 'bg-blue-50 text-blue-700 shadow-sm ring-1 ring-blue-100 dark:bg-blue-950 dark:text-blue-200 dark:ring-blue-900'
                  : 'text-slate-500 hover:bg-white hover:text-slate-900 dark:text-slate-400 dark:hover:bg-gray-900 dark:hover:text-slate-100'
              }`}
            >
              {tab.shortLabel ?? tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {workbenchLeftTab === 'conversations' && <ConversationList />}
        {workbenchLeftTab === 'sources' && (
          <Sidebar isCollapsed={false} onToggle={onToggle} onUploadClick={onUploadClick} />
        )}
        {workbenchLeftTab === 'knowledge_base' && <KnowledgeBaseList />}
      </div>
    </div>
  )
}

function ConversationList() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { openConversationTab, closeConversationTab, setConversationId, setMessages } = useStore()

  const loadConversations = () => {
    setIsLoading(true)
    setError(null)
    chatApi.listConversations()
      .then((data) => setConversations(data.conversations || []))
      .catch((loadError) => {
        console.error('Failed to load conversations:', loadError)
        setError('Conversations could not be loaded')
      })
      .finally(() => setIsLoading(false))
  }

  useEffect(loadConversations, [])

  const openConversation = async (conversation: ConversationSummary) => {
    openConversationTab({ conversation_id: conversation.conversation_id, title: conversation.title })
    setConversationId(conversation.conversation_id)
    const data = await chatApi.getConversation(conversation.conversation_id)
    setMessages((data.messages || []) as Message[])
  }

  const deleteConversation = async (conversation: ConversationSummary) => {
    await chatApi.deleteConversation(conversation.conversation_id)
    setConversations((items) => items.filter((item) => item.conversation_id !== conversation.conversation_id))
    closeConversationTab(conversation.conversation_id)
  }

  return (
    <div data-testid="conversation-list" className="p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Conversations</h2>
        <button type="button" onClick={loadConversations} className="rounded p-1.5 text-slate-500 hover:bg-[#ebeae8]" aria-label="Reload conversations">
          <RotateCcw className="h-3.5 w-3.5" />
        </button>
      </div>
      {isLoading && (
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading conversations
        </div>
      )}
      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
          <p>{error}</p>
          <button type="button" onClick={loadConversations} className="mt-2 font-semibold text-amber-950">Retry</button>
        </div>
      )}
      {!isLoading && !error && conversations.length === 0 && (
        <p className="rounded-lg border border-[#e2e1de] bg-white p-3 text-sm text-slate-500 shadow-sm">No conversations yet</p>
      )}
      <div className="space-y-2">
        {conversations.map((conversation) => (
          <div key={conversation.conversation_id} className="rounded-lg border border-[#e2e1de] bg-white p-3 shadow-sm">
            <button
              type="button"
              aria-label={`Open ${conversation.title}`}
              onClick={() => void openConversation(conversation)}
              className="block w-full text-left"
            >
              <p className="truncate text-sm font-semibold text-slate-900">{conversation.title}</p>
              <p className="mt-1 line-clamp-2 text-xs text-slate-500">{conversation.latest_message || `${conversation.message_count} messages`}</p>
            </button>
            <div className="mt-2 flex justify-end">
              <button
                type="button"
                aria-label={`Delete ${conversation.title}`}
                onClick={() => void deleteConversation(conversation)}
                className="rounded p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function KnowledgeBaseList() {
  const [pages, setPages] = useState<WikiPage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const { selectedWikiPageIds, toggleWikiContext, setPreviewTarget } = useStore()

  useEffect(() => {
    let isMounted = true
    setIsLoading(true)
    wikiApi.list()
      .then((data) => {
        if (isMounted) setPages(data.pages || [])
      })
      .catch((error) => {
        console.error('Failed to load knowledge base pages:', error)
      })
      .finally(() => {
        if (isMounted) setIsLoading(false)
      })
    return () => {
      isMounted = false
    }
  }, [])

  return (
    <div data-testid="kb-context-list" className="p-4">
      <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Knowledge Base</h2>
      {isLoading && (
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading pages
        </div>
      )}
      {!isLoading && pages.length === 0 && (
        <p className="rounded-lg border border-[#e2e1de] bg-white p-3 text-sm text-slate-500 shadow-sm">No wiki pages yet</p>
      )}
      <div className="space-y-2">
        {pages.map((page) => (
          <label key={page.page_id} className="flex cursor-pointer items-start gap-3 rounded-lg border border-[#e2e1de] bg-white p-3 shadow-sm hover:border-blue-200">
            <input
              type="checkbox"
              aria-label={`Use ${page.title}`}
              checked={selectedWikiPageIds.includes(page.page_id)}
              onChange={() => toggleWikiContext(page.page_id)}
              className="mt-1 h-4 w-4 rounded border-[#d8d6d2] text-blue-600"
            />
            <button
              type="button"
              onClick={() => setPreviewTarget({ type: 'wiki', id: page.page_id, title: page.title })}
              className="min-w-0 flex-1 text-left"
            >
              <p className="truncate text-sm font-semibold text-slate-900">{page.title}</p>
              <p className="mt-1 text-xs text-slate-500">{page.source_doc_ids.length} sources</p>
            </button>
          </label>
        ))}
      </div>
    </div>
  )
}
