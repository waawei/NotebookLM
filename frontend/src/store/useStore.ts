import { create } from 'zustand'

export type AppModule = 'dashboard' | 'workbench' | 'sources' | 'notes' | 'wiki' | 'outputs' | 'skills' | 'agents' | 'settings'
export type ThemePreference = 'system' | 'light' | 'dark'
export type ResolvedTheme = 'light' | 'dark'
export type LanguagePreference = 'en' | 'zh-CN'
export type WorkbenchLeftTab = 'conversations' | 'sources' | 'knowledge_base'
export type PreviewTarget = { type: 'document' | 'wiki' | 'note' | 'output'; id: string; title: string } | null

export interface OpenConversationTab {
  conversation_id: string | null
  title: string
  isDirty?: boolean
}

export interface PendingSkillCommand {
  skill_id: string
  text: string
}

const defaultConversationTabs: OpenConversationTab[] = [{ conversation_id: null, title: 'New conversation' }]
const newConversationTabId = 'new'

export function resolveTheme(theme: ThemePreference, systemIsDark: boolean): ResolvedTheme {
  return theme === 'system' ? (systemIsDark ? 'dark' : 'light') : theme
}

function initialThemePreference(): ThemePreference {
  if (typeof window === 'undefined') return 'system'
  const value = localStorage.getItem('theme_preference')
  return value === 'light' || value === 'dark' || value === 'system' ? value : 'system'
}

function initialLanguagePreference(): LanguagePreference {
  if (typeof window === 'undefined') return 'en'
  const value = localStorage.getItem('language_preference')
  return value === 'zh-CN' || value === 'en' ? value : 'en'
}

function readJsonFromStorage<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') return fallback
  try {
    const value = localStorage.getItem(key)
    return value ? JSON.parse(value) as T : fallback
  } catch {
    return fallback
  }
}

function persistJson(key: string, value: unknown) {
  if (typeof window !== 'undefined') {
    localStorage.setItem(key, JSON.stringify(value))
  }
}

function tabId(tab: OpenConversationTab) {
  return tab.conversation_id ?? newConversationTabId
}

export interface Document {
  doc_id: string
  filename: string
  file_type: string
  upload_time: string
  status: string
  total_chunks: number
  summary?: string
  summary_status?: 'pending' | 'available' | 'unavailable'
  summary_error?: string | null
  error_message?: string | null
  space_id?: string | null
  space_ids?: string[]
  tags?: string[]
}

export interface Citation {
  number: number
  doc_id: string
  doc_name: string
  page: number | null
  section?: string | null
  chunk_id: number
  content: string
  relevance_score: number
}

export interface Message {
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
}

interface Toast {
  id: string
  message: string
  type: 'success' | 'error' | 'info'
}

interface AppState {
  activeModule: AppModule
  setActiveModule: (module: AppModule) => void

  documents: Document[]
  selectedDocIds: string[]
  activeSpaceId: string | null
  sourceQuery: string
  sourceStatusFilter: string | null
  sourceTagFilter: string[]
  setDocuments: (documents: Document[]) => void
  addDocument: (document: Document) => void
  removeDocument: (docId: string) => void
  toggleDocumentSelection: (docId: string) => void
  clearSelectedDocs: () => void
  setActiveSpaceId: (spaceId: string | null) => void
  setSourceQuery: (query: string) => void
  setSourceStatusFilter: (status: string | null) => void
  setSourceTagFilter: (tags: string[]) => void

  workbenchLeftTab: WorkbenchLeftTab
  openConversationTabs: OpenConversationTab[]
  activeConversationTabId: string
  previewTarget: PreviewTarget
  selectedWikiPageIds: string[]
  selectedAgentId: string | null
  pendingSkillCommand: PendingSkillCommand | null
  artifactRefreshToken: number
  setWorkbenchLeftTab: (tab: WorkbenchLeftTab) => void
  openConversationTab: (tab: OpenConversationTab) => void
  closeConversationTab: (conversationTabId: string) => void
  setActiveConversationTab: (conversationTabId: string) => void
  setPreviewTarget: (target: PreviewTarget) => void
  toggleWikiContext: (pageId: string) => void
  setSelectedAgentId: (agentId: string | null) => void
  setPendingSkillCommand: (command: PendingSkillCommand) => void
  clearPendingSkillCommand: () => void
  bumpArtifactRefreshToken: () => void

  messages: Message[]
  conversationId: string | null
  isLoading: boolean
  suggestedQuestions: string[]
  addMessage: (message: Message) => void
  updateMessageAtIndex: (index: number, message: Message) => void
  setMessages: (messages: Message[]) => void
  setConversationId: (id: string) => void
  setLoading: (loading: boolean) => void
  setSuggestedQuestions: (questions: string[]) => void
  clearChat: () => void

  toasts: Toast[]
  addToast: (message: string, type?: 'success' | 'error' | 'info') => void
  removeToast: (id: string) => void

  theme: ThemePreference
  setTheme: (theme: ThemePreference) => void
  language: LanguagePreference
  setLanguage: (language: LanguagePreference) => void
}

export const useStore = create<AppState>((set) => ({
  activeModule: 'workbench',
  setActiveModule: (module) => set({ activeModule: module }),

  documents: [],
  selectedDocIds: [],
  activeSpaceId: null,
  sourceQuery: '',
  sourceStatusFilter: null,
  sourceTagFilter: [],

  setDocuments: (documents) => set({ documents }),

  addDocument: (document) =>
    set((state) => ({ documents: [...state.documents, document] })),

  removeDocument: (docId) =>
    set((state) => ({
      documents: state.documents.filter((doc) => doc.doc_id !== docId),
      selectedDocIds: state.selectedDocIds.filter((id) => id !== docId),
    })),

  toggleDocumentSelection: (docId) =>
    set((state) => ({
      selectedDocIds: state.selectedDocIds.includes(docId)
        ? state.selectedDocIds.filter((id) => id !== docId)
        : [...state.selectedDocIds, docId],
    })),

  clearSelectedDocs: () => set({ selectedDocIds: [] }),

  setActiveSpaceId: (spaceId) => set({ activeSpaceId: spaceId }),

  setSourceQuery: (query) => set({ sourceQuery: query }),

  setSourceStatusFilter: (status) => set({ sourceStatusFilter: status }),

  setSourceTagFilter: (tags) => set({ sourceTagFilter: tags }),

  workbenchLeftTab: 'conversations',
  openConversationTabs: readJsonFromStorage<OpenConversationTab[]>('open_conversation_tabs', defaultConversationTabs),
  activeConversationTabId: readJsonFromStorage<string>('active_conversation_tab_id', newConversationTabId),
  previewTarget: null,
  selectedWikiPageIds: readJsonFromStorage<string[]>('selected_wiki_page_ids', []),
  selectedAgentId: typeof window !== 'undefined' ? localStorage.getItem('selected_agent_id') : null,
  pendingSkillCommand: null,
  artifactRefreshToken: 0,

  setWorkbenchLeftTab: (tab) => set({ workbenchLeftTab: tab }),

  openConversationTab: (tab) =>
    set((state) => {
      const nextTab = { conversation_id: tab.conversation_id, title: tab.title, ...(tab.isDirty ? { isDirty: tab.isDirty } : {}) }
      const nextTabId = tabId(nextTab)
      const exists = state.openConversationTabs.some((item) => tabId(item) === nextTabId)
      const openConversationTabs = exists
        ? state.openConversationTabs.map((item) => (tabId(item) === nextTabId ? { ...item, ...nextTab } : item))
        : [...state.openConversationTabs, nextTab]
      persistJson('open_conversation_tabs', openConversationTabs)
      persistJson('active_conversation_tab_id', nextTabId)
      return { openConversationTabs, activeConversationTabId: nextTabId }
    }),

  closeConversationTab: (conversationTabId) =>
    set((state) => {
      const currentIndex = state.openConversationTabs.findIndex((item) => tabId(item) === conversationTabId)
      const remainingTabs = state.openConversationTabs.filter((item) => tabId(item) !== conversationTabId)
      const openConversationTabs = remainingTabs.length > 0 ? remainingTabs : defaultConversationTabs
      let activeConversationTabId = state.activeConversationTabId
      if (state.activeConversationTabId === conversationTabId) {
        const fallbackIndex = Math.min(Math.max(currentIndex, 0), openConversationTabs.length - 1)
        activeConversationTabId = tabId(openConversationTabs[fallbackIndex])
      }
      persistJson('open_conversation_tabs', openConversationTabs)
      persistJson('active_conversation_tab_id', activeConversationTabId)
      return { openConversationTabs, activeConversationTabId }
    }),

  setActiveConversationTab: (conversationTabId) => {
    persistJson('active_conversation_tab_id', conversationTabId)
    set({ activeConversationTabId: conversationTabId })
  },

  setPreviewTarget: (target) => set({ previewTarget: target }),

  toggleWikiContext: (pageId) =>
    set((state) => {
      const selectedWikiPageIds = state.selectedWikiPageIds.includes(pageId)
        ? state.selectedWikiPageIds.filter((id) => id !== pageId)
        : [...state.selectedWikiPageIds, pageId]
      persistJson('selected_wiki_page_ids', selectedWikiPageIds)
      return { selectedWikiPageIds }
    }),

  setSelectedAgentId: (agentId) => {
    if (typeof window !== 'undefined') {
      if (agentId) {
        localStorage.setItem('selected_agent_id', agentId)
      } else {
        localStorage.removeItem('selected_agent_id')
      }
    }
    set({ selectedAgentId: agentId })
  },

  setPendingSkillCommand: (command) => set({ pendingSkillCommand: command }),

  clearPendingSkillCommand: () => set({ pendingSkillCommand: null }),

  bumpArtifactRefreshToken: () =>
    set((state) => ({ artifactRefreshToken: state.artifactRefreshToken + 1 })),

  messages: typeof window !== 'undefined'
    ? JSON.parse(localStorage.getItem('chat_messages') || '[]')
    : [],
  conversationId: typeof window !== 'undefined'
    ? localStorage.getItem('conversation_id')
    : null,
  isLoading: false,
  suggestedQuestions: [],

  addMessage: (message) =>
    set((state) => {
      const newMessages = [...state.messages, message]
      if (typeof window !== 'undefined') {
        localStorage.setItem('chat_messages', JSON.stringify(newMessages))
      }
      return { messages: newMessages }
    }),

  updateMessageAtIndex: (index, message) =>
    set((state) => {
      const newMessages = [...state.messages]
      newMessages[index] = message
      if (typeof window !== 'undefined') {
        localStorage.setItem('chat_messages', JSON.stringify(newMessages))
      }
      return { messages: newMessages }
    }),

  setMessages: (messages) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('chat_messages', JSON.stringify(messages))
    }
    set({ messages })
  },

  setConversationId: (id) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('conversation_id', id)
    }
    set({ conversationId: id })
  },

  setLoading: (loading) => set({ isLoading: loading }),

  setSuggestedQuestions: (questions) => set({ suggestedQuestions: questions }),

  clearChat: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('chat_messages')
      localStorage.removeItem('conversation_id')
    }
    set({
      messages: [],
      conversationId: null,
      isLoading: false,
      suggestedQuestions: [],
      activeConversationTabId: newConversationTabId,
    })
    persistJson('active_conversation_tab_id', newConversationTabId)
  },

  toasts: [],

  addToast: (message, type = 'info') =>
    set((state) => {
      const id = Date.now().toString()
      return {
        toasts: [...state.toasts, { id, message, type }]
      }
    }),

  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((toast) => toast.id !== id)
    })),

  theme: initialThemePreference(),

  setTheme: (theme) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('theme_preference', theme)
    }
    set({ theme })
  },

  language: initialLanguagePreference(),

  setLanguage: (language) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('language_preference', language)
    }
    set({ language })
  },
}))
