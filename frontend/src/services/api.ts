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
  error_message?: string | null
  space_id?: string | null
  space_ids?: string[]
  tags?: string[]
}

export interface DocumentSearchFilters {
  query?: string
  space_id?: string | null
  tags?: string[]
  status?: string | null
}

export interface SpaceItem {
  space_id: string
  name: string
  description: string
  created_at: string
  updated_at: string
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
  mode?: 'review' | 'paper' | 'knowledge_base'
}

export interface NoteItem {
  note_id: string
  title: string
  content: string
  doc_ids: string[]
  conversation_id?: string | null
  links?: Array<{ source_type: string; source_id: string }>
  created_at: string
  updated_at: string
}

export interface NoteCreateRequest {
  title: string
  content: string
  doc_ids?: string[]
  conversation_id?: string | null
}

export interface NoteFromMessageRequest {
  message_index: number
  conversation_id: string
  title: string
  content: string
  doc_ids?: string[]
}

export interface NoteUpdateRequest {
  title?: string
  content?: string
  doc_ids?: string[]
  conversation_id?: string | null
}

export interface OutputItem {
  output_id: string
  kind: string
  title: string
  content: string
  source_doc_ids: string[]
  created_at: string
  updated_at: string
}

export interface OutputExport {
  filename: string
  content_type: string
  content: string
}

export interface WikiPage {
  page_id: string
  title: string
  content: string
  source_doc_ids: string[]
  created_at: string
  updated_at: string
}

export interface WikiPageCreateRequest {
  title: string
  content: string
  source_doc_ids?: string[]
}

export interface WikiPageUpdateRequest {
  title: string
  content: string
}

export interface WikiPageGenerateRequest {
  title: string
  source_doc_ids: string[]
}

export interface SettingsStatus {
  provider: string
  model: string
  base_url_configured: boolean
  api_key_configured: boolean
  temperature: number
  max_tokens: number
  top_k: number
  embedding_model: string
  embedding_device: string
  warnings: string[]
}

export interface SettingsTestResult {
  ok: boolean
  message: string
}

export interface SettingsConfigUpdate {
  provider: string
  model: string
  base_url: string
  api_key?: string
}

export interface SkillItem {
  skill_id: string
  name: string
  description: string
  allowed_tools: string[]
  prompt_template: string
  output_kind: string
}

export interface AgentStep {
  step_id: string
  step_index: number
  kind: string
  title: string
  payload: Record<string, unknown>
  created_at: string
}

export interface AgentRun {
  run_id: string
  skill_id: string
  status: 'running' | 'completed' | 'failed'
  input_payload: { doc_ids?: string[]; request?: string }
  output_id?: string | null
  error?: string | null
  created_at?: string
  updated_at?: string
  steps: AgentStep[]
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

  search: async (filters: DocumentSearchFilters): Promise<{ documents: DocumentItem[]; total: number }> => {
    const response = await api.post('/documents/search', filters)
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

export const spacesApi = {
  list: async (): Promise<{ spaces: SpaceItem[] }> => {
    const response = await api.get('/spaces')
    return response.data
  },

  create: async (data: { name: string; description?: string }): Promise<SpaceItem> => {
    const response = await api.post('/spaces', data)
    return response.data
  },

  assignDocument: async (spaceId: string, docId: string): Promise<{ message: string }> => {
    const response = await api.post(`/spaces/${spaceId}/documents/${docId}`)
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

  createFromMessage: async (data: NoteFromMessageRequest): Promise<{ note_id: string; message: string }> => {
    const response = await api.post('/notes/from-message', data)
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

export const outputApi = {
  list: async (kind?: string): Promise<{ outputs: OutputItem[]; total: number }> => {
    const response = await api.get('/outputs', {
      params: kind ? { kind } : undefined,
    })
    return response.data
  },

  generate: async (data: { kind: string; source_doc_ids: string[] }): Promise<OutputItem> => {
    const response = await api.post('/outputs/generate', data)
    return response.data
  },

  get: async (outputId: string): Promise<OutputItem> => {
    const response = await api.get(`/outputs/${outputId}`)
    return response.data
  },

  delete: async (outputId: string): Promise<{ message: string }> => {
    const response = await api.delete(`/outputs/${outputId}`)
    return response.data
  },

  export: async (outputId: string): Promise<OutputExport> => {
    const response = await api.post(`/outputs/${outputId}/export`)
    return response.data
  },
}

export const wikiApi = {
  list: async (): Promise<{ pages: WikiPage[]; total: number }> => {
    const response = await api.get('/wiki/pages')
    return response.data
  },

  create: async (data: WikiPageCreateRequest): Promise<WikiPage> => {
    const response = await api.post('/wiki/pages', data)
    return response.data
  },

  get: async (pageId: string): Promise<WikiPage> => {
    const response = await api.get(`/wiki/pages/${pageId}`)
    return response.data
  },

  update: async (pageId: string, data: WikiPageUpdateRequest): Promise<{ message: string }> => {
    const response = await api.put(`/wiki/pages/${pageId}`, data)
    return response.data
  },

  generate: async (data: WikiPageGenerateRequest): Promise<WikiPage> => {
    const response = await api.post('/wiki/generate', data)
    return response.data
  },

  export: async (pageId: string): Promise<OutputExport> => {
    const response = await api.post(`/wiki/pages/${pageId}/export`)
    return response.data
  },
}

export const settingsApi = {
  getStatus: async (): Promise<SettingsStatus> => {
    const response = await api.get('/settings/status')
    return response.data
  },

  save: async (data: SettingsConfigUpdate): Promise<SettingsStatus> => {
    const response = await api.put('/settings/llm', data)
    return response.data
  },

  clear: async (): Promise<SettingsStatus> => {
    const response = await api.delete('/settings/llm')
    return response.data
  },

  testLlm: async (): Promise<SettingsTestResult> => {
    const response = await api.post('/settings/test-llm')
    return response.data
  },
}

export const skillsApi = {
  list: async (): Promise<{ skills: SkillItem[] }> => {
    const response = await api.get('/skills')
    return response.data
  },

  get: async (skillId: string): Promise<SkillItem> => {
    const response = await api.get(`/skills/${skillId}`)
    return response.data
  },
}

export const agentsApi = {
  listRuns: async (): Promise<{ runs: AgentRun[]; total: number }> => {
    const response = await api.get('/agents/runs')
    return response.data
  },

  createRun: async (data: { skill_id: string; doc_ids: string[]; request?: string }): Promise<AgentRun> => {
    const response = await api.post('/agents/runs', data)
    return response.data
  },

  getRun: async (runId: string): Promise<AgentRun> => {
    const response = await api.get(`/agents/runs/${runId}`)
    return response.data
  },
}

export default api
