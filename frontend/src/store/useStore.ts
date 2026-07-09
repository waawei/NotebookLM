import { create } from 'zustand'

interface Document {
  doc_id: string
  filename: string
  file_type: string
  upload_time: string
  status: string
  total_chunks: number
  summary?: string  // 文档摘要
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
}

interface Citation {
  number: number  // 引用编号 [1], [2], [3]...
  doc_id: string
  doc_name: string
  page: number | null
  chunk_id: number
  content: string
  relevance_score: number
}

interface Toast {
  id: string
  message: string
  type: 'success' | 'error' | 'info'
}

interface AppState {
  // 文档状态
  documents: Document[]
  selectedDocIds: string[]
  setDocuments: (documents: Document[]) => void
  addDocument: (document: Document) => void
  removeDocument: (docId: string) => void
  toggleDocumentSelection: (docId: string) => void
  clearSelectedDocs: () => void

  // 对话状态
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

  // Toast 通知
  toasts: Toast[]
  addToast: (message: string, type?: 'success' | 'error' | 'info') => void
  removeToast: (id: string) => void

  // 主题
  isDarkMode: boolean
  toggleDarkMode: () => void
}

export const useStore = create<AppState>((set) => ({
  // 文档状态初始值
  documents: [],
  selectedDocIds: [],

  // 文档操作
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

  // 对话状态初始值（从 localStorage 恢复）
  messages: typeof window !== 'undefined'
    ? JSON.parse(localStorage.getItem('chat_messages') || '[]')
    : [],
  conversationId: typeof window !== 'undefined'
    ? localStorage.getItem('conversation_id')
    : null,
  isLoading: false,
  suggestedQuestions: [],

  // 对话操作
  addMessage: (message) =>
    set((state) => {
      const newMessages = [...state.messages, message]
      // 持久化到 localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem('chat_messages', JSON.stringify(newMessages))
      }
      return { messages: newMessages }
    }),

  updateMessageAtIndex: (index, message) =>
    set((state) => {
      const newMessages = [...state.messages]
      newMessages[index] = message
      // 持久化到 localStorage
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

  // Toast 通知
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

  // 主题（从 localStorage 恢复）
  isDarkMode: typeof window !== 'undefined'
    ? localStorage.getItem('dark_mode') === 'true'
    : false,

  toggleDarkMode: () =>
    set((state) => {
      const newDarkMode = !state.isDarkMode
      if (typeof window !== 'undefined') {
        localStorage.setItem('dark_mode', String(newDarkMode))
        // 更新 document root 的 class
        if (newDarkMode) {
          document.documentElement.classList.add('dark')
        } else {
          document.documentElement.classList.remove('dark')
        }
      }
      return { isDarkMode: newDarkMode }
    }),
}))
