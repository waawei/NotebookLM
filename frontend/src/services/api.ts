import axios from 'axios'

export const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface DocumentItem {
  doc_id: string
  filename: string
  file_type: string
  upload_time: string
  status: string
  total_chunks: number
  summary?: string
}

export interface UploadResponse {
  doc_id: string
  filename: string
  status: string
  message: string
}

export interface ChatAskRequest {
  question: string
  doc_ids?: string[]
  conversation_id?: string | null
  history?: Array<{ role: string; content: string }>
}

export interface NoteItem {
  note_id: string
  title: string
  content: string
  doc_ids: string[]
  conversation_id?: string | null
  created_at: string
  updated_at: string
}

export interface NoteCreateRequest {
  title: string
  content: string
  doc_ids?: string[]
  conversation_id?: string | null
}

export interface NoteUpdateRequest {
  title?: string
  content?: string
  doc_ids?: string[]
  conversation_id?: string | null
}

export const documentApi = {
  upload: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  uploadUrl: async (url: string): Promise<UploadResponse> => {
    const response = await api.post('/documents/upload-url', null, {
      params: { url },
    })
    return response.data
  },

  list: async (): Promise<{ documents: DocumentItem[]; total: number }> => {
    const response = await api.get('/documents/list')
    return response.data
  },

  get: async (docId: string): Promise<DocumentItem> => {
    const response = await api.get(`/documents/${docId}`)
    return response.data
  },

  delete: async (docId: string) => {
    const response = await api.delete(`/documents/${docId}`)
    return response.data
  },

  getStatus: async (docId: string) => {
    const response = await api.get(`/documents/${docId}/status`)
    return response.data
  },
}

export const chatApi = {
  ask: async (data: ChatAskRequest) => {
    const response = await api.post('/chat/ask', data)
    return response.data
  },

  createStreamRequest: async (data: ChatAskRequest): Promise<Response> => {
    return fetch(`${API_BASE_URL}/chat/ask-stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
  },

  suggestQuestions: async (docIds: string[]): Promise<{ questions: string[] }> => {
    const response = await api.post('/chat/suggest-questions', docIds)
    return response.data
  },

  getConversation: async (conversationId: string) => {
    const response = await api.get(`/chat/conversations/${conversationId}`)
    return response.data
  },

  deleteConversation: async (conversationId: string) => {
    const response = await api.delete(`/chat/conversations/${conversationId}`)
    return response.data
  },
}

export const noteApi = {
  create: async (data: NoteCreateRequest): Promise<{ note_id: string; message: string }> => {
    const response = await api.post('/notes/create', data)
    return response.data
  },

  list: async (): Promise<{ notes: NoteItem[]; total: number }> => {
    const response = await api.get('/notes/list')
    return response.data
  },

  get: async (noteId: string): Promise<NoteItem> => {
    const response = await api.get(`/notes/${noteId}`)
    return response.data
  },

  update: async (noteId: string, data: NoteUpdateRequest): Promise<{ message: string }> => {
    const response = await api.put(`/notes/${noteId}`, data)
    return response.data
  },

  delete: async (noteId: string): Promise<{ message: string }> => {
    const response = await api.delete(`/notes/${noteId}`)
    return response.data
  },
}

export default api
