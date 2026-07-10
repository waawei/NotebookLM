import { Plus, X } from 'lucide-react'
import { useStore } from '../store/useStore'

function tabId(tab: { conversation_id: string | null }) {
  return tab.conversation_id ?? 'new'
}

export default function ConversationTabStrip() {
  const {
    openConversationTabs,
    activeConversationTabId,
    setActiveConversationTab,
    closeConversationTab,
    openConversationTab,
    clearChat,
  } = useStore()

  const startNewConversation = () => {
    clearChat()
    openConversationTab({ conversation_id: null, title: 'New conversation' })
    setActiveConversationTab('new')
  }

  return (
    <div
      data-testid="conversation-tab-strip"
      className="flex h-11 shrink-0 items-center gap-2 overflow-x-auto border-b border-[#e2e1de] bg-[#f8f7f6] px-4 dark:border-gray-800 dark:bg-gray-950"
    >
      <div className="flex min-w-0 flex-1 items-center gap-2">
        {openConversationTabs.map((tab) => {
          const id = tabId(tab)
          const isActive = activeConversationTabId === id
          return (
            <div key={id} className="group flex h-8 shrink-0 items-center">
              <button
                type="button"
                aria-label={id === 'new' ? `Conversation tab ${tab.title}` : undefined}
                onClick={() => setActiveConversationTab(id)}
                className={`h-8 max-w-[11rem] truncate rounded-l-md border px-3 text-xs font-semibold transition-colors ${
                  isActive
                    ? 'border-blue-100 bg-blue-50 text-blue-700 shadow-sm dark:border-blue-900 dark:bg-blue-950 dark:text-blue-200'
                    : 'border-transparent text-slate-500 hover:bg-white hover:text-slate-800 dark:text-slate-400 dark:hover:bg-gray-900 dark:hover:text-slate-100'
                }`}
              >
                {tab.title}
              </button>
              <button
                type="button"
                aria-label={`Close ${tab.title}`}
                onClick={(event) => {
                  event.stopPropagation()
                  closeConversationTab(id)
                }}
                className={`flex h-8 w-7 items-center justify-center rounded-r-md border-y border-r transition-colors ${
                  isActive
                    ? 'border-blue-100 bg-blue-50 text-blue-600 hover:bg-blue-100 dark:border-blue-900 dark:bg-blue-950 dark:text-blue-200'
                    : 'border-transparent text-slate-400 hover:bg-white hover:text-slate-700 dark:text-slate-500 dark:hover:bg-gray-900 dark:hover:text-slate-100'
                }`}
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          )
        })}
      </div>
      <button
        type="button"
        aria-label="New conversation"
        onClick={startNewConversation}
        className="flex h-8 shrink-0 items-center gap-1.5 rounded-md border border-[#e2e1de] bg-white px-3 text-xs font-semibold text-slate-700 shadow-sm hover:border-blue-200 hover:text-blue-700 dark:border-gray-800 dark:bg-gray-900 dark:text-slate-200"
      >
        <Plus className="h-3.5 w-3.5" />
        New
      </button>
    </div>
  )
}
