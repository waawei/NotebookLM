import { create } from 'zustand'

export type AppModule = 'dashboard' | 'workbench' | 'sources' | 'notes' | 'wiki' | 'outputs' | 'settings'

export interface Document {
  doc_id: string
  filename: string
  file_type: string
  upload_time: string
  status: string
  total_chunks: number
  summary?: string
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

  isDarkMode: boolean
  toggleDarkMode: () => void
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
    })
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

  isDarkMode: typeof window !== 'undefined'
    ? localStorage.getItem('dark_mode') === 'true'
    : false,

  toggleDarkMode: () =>
    set((state) => {
      const newDarkMode = !state.isDarkMode
      if (typeof window !== 'undefined') {
        localStorage.setItem('dark_mode', String(newDarkMode))
        if (newDarkMode) {
          document.documentElement.classList.add('dark')
        } else {
          document.documentElement.classList.remove('dark')
        }
      }
      return { isDarkMode: newDarkMode }
    }),
}))
