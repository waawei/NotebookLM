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
  summary_status?: 'pending' | 'available' | 'unavailable'
  summary_error?: string | null
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
  status?: 'active' | 'archived' | 'deleted'
  deleted_at?: string | null
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

export type PreviewTargetType = 'document' | 'wiki' | 'note' | 'output'

export interface PreviewLink {
  type: string
  id: string
  title: string
}

export interface PreviewItem {
  type: PreviewTargetType
  id: string
  title: string
  content_preview: string
  metadata: Record<string, unknown>
  links: PreviewLink[]
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
  endpoint_mode: SettingsEndpointMode
  warnings: string[]
}

export interface ConversationSummary {
  conversation_id: string
  title: string
  updated_at: string
  message_count: number
  latest_message?: string | null
}

interface RawConversationSummary extends Partial<ConversationSummary> {
  id?: string
  last_message?: string | null
}

export type SettingsEndpointMode = 'auto' | 'exact'

export type SettingsConnectionDiagnosticCategory =
  | 'authentication_failed'
  | 'permission_denied'
  | 'model_not_found'
  | 'invalid_request'
  | 'rate_limited'
  | 'upstream_unavailable'
  | 'connection_failed'
  | 'timed_out'
  | 'unknown'

export interface SettingsConnectionDiagnostic {
  phase: 'chat_completion'
  status_code: number | null
  category: SettingsConnectionDiagnosticCategory
  summary: string
}

export interface ChatStreamErrorEvent {
  type: 'error'
  message: string
  diagnostic?: SettingsConnectionDiagnostic | null
}

export interface SettingsTestResult {
  ok: boolean
  message: string
  diagnostic?: SettingsConnectionDiagnostic | null
}

export interface SettingsConfigUpdate {
  provider: string
  model: string
  base_url?: string
  api_key?: string
  endpoint_mode?: SettingsEndpointMode
}

export interface SettingsModelDiscoveryRequest {
  provider?: string
  base_url?: string
  api_key?: string
  endpoint_mode?: SettingsEndpointMode
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

export interface ModelingProject {
  project_id: string
  name: string
  slug: string
  workspace_path: string
  state: string
  deadline?: string | null
  created_at?: string
  updated_at?: string
}

export interface ModelingArtifact {
  artifact_id: string
  project_id: string
  artifact_type: string
  relative_path: string
  sha256: string
  source_run_id?: string | null
  source_experiment_id?: string | null
  version: number
  created_at: string
  content?: unknown
}

export interface ApprovalRequest {
  approval_id: string
  project_id: string
  gate: string
  payload_hash: string
  payload: {
    artifact_id?: string
    artifact_sha256?: string
    version?: number
  }
  status: string
  created_at?: string
  updated_at?: string
}

export interface ModelCandidate {
  name: string
  assumptions: string[]
  features: string[]
  algorithm: string
  metrics: string[]
  risks: string[]
}

export interface ModelPlan {
  problem_summary: string
  candidates: ModelCandidate[]
}

export interface ExecutionBatch {
  experiment_id: string
  commands: string[][]
  timeout_seconds: number
  max_output_bytes: number
  network_allowed: boolean
  code_hash: string
  input_hashes: Record<string, string>
  source_hashes: Record<string, string>
}

export interface ExperimentRun {
  experiment_id: string
  project_id: string
  config: { model: { kind: string }; seed: number; metrics: Array<{ name: string; direction: string }> }
  execution_payload_hash?: string | null
  execution_batch?: ExecutionBatch
  status: string
  pid?: number | null
  exit_code?: number | null
  error_code?: string | null
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

  listConversations: async (): Promise<{ conversations: ConversationSummary[] }> => {
    const response = await api.get('/chat/conversations')
    return {
      conversations: (response.data.conversations || []).map((conversation: RawConversationSummary) => ({
        conversation_id: conversation.conversation_id || conversation.id || '',
        title: conversation.title || 'Untitled conversation',
        updated_at: conversation.updated_at || '',
        message_count: conversation.message_count || 0,
        latest_message: conversation.latest_message ?? conversation.last_message ?? null,
      })),
    }
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
  list: async (kind?: string, includeArchived = false): Promise<{ outputs: OutputItem[]; total: number }> => {
    const response = await api.get('/outputs', {
      params: {
        ...(kind ? { kind } : {}),
        ...(includeArchived ? { include_archived: true } : {}),
      },
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

  archive: async (outputId: string): Promise<{ message: string }> => {
    const response = await api.post(`/outputs/${outputId}/archive`)
    return response.data
  },

  restore: async (outputId: string): Promise<{ message: string }> => {
    const response = await api.post(`/outputs/${outputId}/restore`)
    return response.data
  },
}

export const previewApi = {
  get: async (targetType: PreviewTargetType, targetId: string): Promise<PreviewItem> => {
    const response = await api.get(`/preview/${targetType}/${targetId}`)
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

  testLlm: async (data?: SettingsConfigUpdate): Promise<SettingsTestResult> => {
    const response = await api.post('/settings/test-llm', data)
    return response.data
  },

  listModels: async (data: SettingsModelDiscoveryRequest): Promise<{ models: string[] }> => {
    const response = await api.post('/settings/models', data)
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

export const modelingApi = {
  list: async (): Promise<{ projects: ModelingProject[]; total: number }> => (await api.get('/modeling/projects')).data,
  create: async (data: { name: string; deadline?: string }): Promise<ModelingProject> => (await api.post('/modeling/projects', data)).data,
  get: async (projectId: string): Promise<ModelingProject> => (await api.get(`/modeling/projects/${projectId}`)).data,
  advance: async (projectId: string): Promise<ModelingProject> => (await api.post(`/modeling/projects/${projectId}/advance`)).data,
  rollback: async (projectId: string, reason: string): Promise<ModelingProject> => (await api.post(`/modeling/projects/${projectId}/rollback`, { reason })).data,
  uploadInput: async (projectId: string, kind: 'problem' | 'data', file: File): Promise<ModelingArtifact> => {
    const formData = new FormData()
    formData.append('file', file)
    return (await api.post(`/modeling/projects/${projectId}/inputs`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params: { kind },
    })).data
  },
  parseProblem: async (projectId: string) => (await api.post(`/modeling/projects/${projectId}/problem/parse`)).data,
  profileData: async (projectId: string, artifactId: string) => (await api.post(`/modeling/projects/${projectId}/data/profile/${artifactId}`)).data,
  createModelPlan: async (projectId: string) => (await api.post(`/modeling/projects/${projectId}/model-plan`)).data,
  listArtifacts: async (projectId: string): Promise<{ artifacts: ModelingArtifact[]; total: number }> => (await api.get(`/modeling/projects/${projectId}/artifacts`)).data,
  getArtifact: async (projectId: string, artifactId: string): Promise<ModelingArtifact> => (await api.get(`/modeling/projects/${projectId}/artifacts/${artifactId}`)).data,
  listApprovals: async (projectId: string): Promise<{ approvals: ApprovalRequest[]; total: number }> => (await api.get(`/modeling/projects/${projectId}/approvals`)).data,
  decideApproval: async (
    projectId: string,
    approvalId: string,
    decision: { decision: 'approved' | 'changes_requested' | 'rejected'; payload_hash: string; comment: string },
  ) => (await api.post(`/modeling/projects/${projectId}/approvals/${approvalId}/decide`, decision)).data,
  prepareExperiment: async (projectId: string, candidateIndex: number) => (await api.post(`/modeling/projects/${projectId}/experiments/prepare`, null, { params: { candidate_index: candidateIndex } })).data,
  listExperiments: async (projectId: string): Promise<{ experiments: ExperimentRun[]; total: number }> => (await api.get(`/modeling/projects/${projectId}/experiments`)).data,
  requestExecution: async (projectId: string, experimentId: string): Promise<ApprovalRequest> => (await api.post(`/modeling/projects/${projectId}/experiments/${experimentId}/request-execution`)).data,
  executeExperiment: async (projectId: string, experimentId: string): Promise<ExperimentRun> => (await api.post(`/modeling/projects/${projectId}/experiments/${experimentId}/execute`)).data,
}

export default api
