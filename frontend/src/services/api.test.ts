import { beforeEach, describe, expect, it, vi } from 'vitest'

const httpClient = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
}))

vi.mock('axios', () => ({
  default: {
    create: () => httpClient,
  },
}))

import { chatApi, modelingApi, outputApi, previewApi, settingsApi } from './api'

const safeStatus = {
  provider: 'openai',
  model: 'gpt-test',
  base_url_configured: false,
  api_key_configured: true,
  temperature: 0.7,
  max_tokens: 2000,
  top_k: 5,
  embedding_model: 'embedding-model',
  embedding_device: 'cpu',
  warnings: [],
}

describe('settingsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('sends the API key only in the save request and returns safe status', async () => {
    const writeKey = 'browser-only-secret'
    const setItem = vi.spyOn(Storage.prototype, 'setItem')
    httpClient.put.mockResolvedValue({ data: safeStatus })

    const status = await settingsApi.save({
      provider: 'openai',
      model: 'gpt-test',
      base_url: '',
      api_key: writeKey,
    })

    expect(httpClient.put).toHaveBeenCalledWith('/settings/llm', {
      provider: 'openai',
      model: 'gpt-test',
      base_url: '',
      api_key: writeKey,
    })
    expect(status).toEqual(safeStatus)
    expect(JSON.stringify(status)).not.toContain(writeKey)
    expect(setItem).not.toHaveBeenCalled()
    setItem.mockRestore()
  })

  it('sends a temporary key only in the model discovery request', async () => {
    const temporaryKey = 'temporary-browser-key'
    httpClient.post.mockResolvedValue({ data: { models: ['a-model'] } })

    const result = await settingsApi.listModels({
      provider: 'openai_compatible',
      base_url: 'https://gateway.test',
      endpoint_mode: 'auto',
      api_key: temporaryKey,
    })

    expect(httpClient.post).toHaveBeenCalledWith('/settings/models', {
      provider: 'openai_compatible',
      base_url: 'https://gateway.test',
      endpoint_mode: 'auto',
      api_key: temporaryKey,
    })
    expect(result).toEqual({ models: ['a-model'] })
    expect(JSON.stringify(result)).not.toContain(temporaryKey)
  })

  it('sends current form values only in the test connection request', async () => {
    httpClient.post.mockResolvedValue({ data: { ok: true, message: 'LLM connection succeeded' } })

    const result = await settingsApi.testLlm({
      provider: 'ollama',
      model: 'qwen3:8b',
      base_url: 'http://localhost:11434',
      endpoint_mode: 'auto',
    })

    expect(httpClient.post).toHaveBeenCalledWith('/settings/test-llm', {
      provider: 'ollama',
      model: 'qwen3:8b',
      base_url: 'http://localhost:11434',
      endpoint_mode: 'auto',
    })
    expect(result).toEqual({ ok: true, message: 'LLM connection succeeded' })
  })
})

describe('chatApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads conversation summaries from the backend conversation endpoint', async () => {
    httpClient.get.mockResolvedValue({
      data: {
        conversations: [
          {
            conversation_id: 'conv-1',
            title: 'Paper notes',
            updated_at: '2026-07-10T10:00:00',
            message_count: 2,
            latest_message: 'Summarize chapter 2',
          },
        ],
      },
    })

    const result = await chatApi.listConversations()

    expect(httpClient.get).toHaveBeenCalledWith('/chat/conversations')
    expect(result.conversations[0].title).toBe('Paper notes')
  })

  it('normalizes legacy conversation id and last message fields', async () => {
    httpClient.get.mockResolvedValue({
      data: {
        conversations: [
          {
            id: 'conv-legacy',
            title: 'Legacy chat',
            updated_at: '2026-07-10T10:00:00',
            message_count: 1,
            last_message: 'Last question',
          },
        ],
      },
    })

    const result = await chatApi.listConversations()

    expect(result.conversations[0]).toMatchObject({
      conversation_id: 'conv-legacy',
      latest_message: 'Last question',
    })
  })
})

describe('previewApi and output lifecycle', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads typed preview data for a target', async () => {
    httpClient.get.mockResolvedValue({
      data: {
        type: 'wiki',
        id: 'wiki-1',
        title: 'Retrieval Notes',
        content_preview: '# Retrieval',
        metadata: { source_count: 1 },
        links: [{ type: 'document', id: 'doc-1', title: 'doc-1' }],
      },
    })

    const result = await previewApi.get('wiki', 'wiki-1')

    expect(httpClient.get).toHaveBeenCalledWith('/preview/wiki/wiki-1')
    expect(result.title).toBe('Retrieval Notes')
  })

  it('passes archived filters and lifecycle actions to output endpoints', async () => {
    httpClient.get.mockResolvedValue({ data: { outputs: [], total: 0 } })
    httpClient.post.mockResolvedValue({ data: { message: 'ok' } })

    await outputApi.list(undefined, true)
    await outputApi.archive('out-1')
    await outputApi.restore('out-1')

    expect(httpClient.get).toHaveBeenCalledWith('/outputs', { params: { include_archived: true } })
    expect(httpClient.post).toHaveBeenCalledWith('/outputs/out-1/archive')
    expect(httpClient.post).toHaveBeenCalledWith('/outputs/out-1/restore')
  })
})

describe('modelingApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('uses the modeling project endpoints for the complete workflow', async () => {
    const project = {
      project_id: 'project-1',
      name: 'Forecast',
      slug: 'forecast',
      workspace_path: 'C:/projects/forecast',
      state: 'project_initialized',
    }
    httpClient.get.mockResolvedValueOnce({ data: { projects: [project], total: 1 } })
    httpClient.post.mockResolvedValue({ data: project })
    httpClient.get.mockResolvedValueOnce({ data: project })

    await expect(modelingApi.list()).resolves.toEqual({ projects: [project], total: 1 })
    await expect(modelingApi.create({ name: 'Forecast' })).resolves.toEqual(project)
    await expect(modelingApi.get('project-1')).resolves.toEqual(project)
    await expect(modelingApi.advance('project-1')).resolves.toEqual(project)
    await expect(modelingApi.rollback('project-1', 'Need another pass')).resolves.toEqual(project)

    expect(httpClient.get).toHaveBeenNthCalledWith(1, '/modeling/projects')
    expect(httpClient.post).toHaveBeenNthCalledWith(1, '/modeling/projects', { name: 'Forecast' })
    expect(httpClient.get).toHaveBeenNthCalledWith(2, '/modeling/projects/project-1')
    expect(httpClient.post).toHaveBeenNthCalledWith(2, '/modeling/projects/project-1/advance')
    expect(httpClient.post).toHaveBeenNthCalledWith(3, '/modeling/projects/project-1/rollback', { reason: 'Need another pass' })
  })

  it('loads runtime readiness and retains recovery history until dismissal', async () => {
    const runtime = {
      workspace: { configured: true, writable: true },
      python: { available: true, version: '3.12.0' },
      git: { available: true, version: 'git version 2.45.0' },
      xelatex: { available: false, version: null },
    }
    const recoveries = {
      recoveries: [{
        recovery_id: 'recovery-1',
        project_id: 'project-1',
        from_state: 'experiment_running',
        to_state: 'experiment_implementation',
        interrupted_run_ids: ['exp-0001'],
        created_at: '2026-07-12T00:00:00',
      }],
      total: 1,
    }
    httpClient.get.mockResolvedValueOnce({ data: runtime }).mockResolvedValueOnce({ data: recoveries })
    httpClient.post.mockResolvedValueOnce({ data: { ...recoveries.recoveries[0], dismissed_at: '2026-07-12T00:01:00' } })

    await expect(modelingApi.runtime()).resolves.toEqual(runtime)
    await expect(modelingApi.recoveries()).resolves.toEqual(recoveries)
    await expect(modelingApi.dismissRecovery('recovery-1')).resolves.toMatchObject({ recovery_id: 'recovery-1' })

    expect(httpClient.get).toHaveBeenCalledWith('/modeling/runtime')
    expect(httpClient.get).toHaveBeenCalledWith('/modeling/recoveries')
    expect(httpClient.post).toHaveBeenCalledWith('/modeling/recoveries/recovery-1/dismiss')
  })

  it('uses intake, artifact, planning, and approval endpoints', async () => {
    const artifact = { artifact_id: 'artifact-1', project_id: 'project-1', artifact_type: 'data_input' }
    const approval = { approval_id: 'approval-1', project_id: 'project-1', payload_hash: 'hash-1' }
    httpClient.post.mockResolvedValue({ data: artifact })
    httpClient.get
      .mockResolvedValueOnce({ data: { artifacts: [artifact], total: 1 } })
      .mockResolvedValueOnce({ data: artifact })
      .mockResolvedValueOnce({ data: { approvals: [approval], total: 1 } })
    const file = new File(['x,y\n1,2\n'], 'train.csv', { type: 'text/csv' })

    await modelingApi.uploadInput('project-1', 'data', file)
    await modelingApi.parseProblem('project-1')
    await modelingApi.profileData('project-1', 'artifact-1')
    await modelingApi.createModelPlan('project-1')
    await modelingApi.listArtifacts('project-1')
    await modelingApi.getArtifact('project-1', 'artifact-1')
    await modelingApi.listApprovals('project-1')
    await modelingApi.decideApproval('project-1', 'approval-1', {
      decision: 'approved',
      payload_hash: 'hash-1',
      comment: 'ok',
    })

    expect(httpClient.post).toHaveBeenCalledWith(
      '/modeling/projects/project-1/inputs',
      expect.any(FormData),
      { headers: { 'Content-Type': 'multipart/form-data' }, params: { kind: 'data' } },
    )
    expect(httpClient.post).toHaveBeenCalledWith('/modeling/projects/project-1/problem/parse')
    expect(httpClient.post).toHaveBeenCalledWith('/modeling/projects/project-1/data/profile/artifact-1')
    expect(httpClient.post).toHaveBeenCalledWith('/modeling/projects/project-1/model-plan')
    expect(httpClient.get).toHaveBeenCalledWith('/modeling/projects/project-1/artifacts')
    expect(httpClient.get).toHaveBeenCalledWith('/modeling/projects/project-1/artifacts/artifact-1')
    expect(httpClient.get).toHaveBeenCalledWith('/modeling/projects/project-1/approvals')
    expect(httpClient.post).toHaveBeenCalledWith(
      '/modeling/projects/project-1/approvals/approval-1/decide',
      { decision: 'approved', payload_hash: 'hash-1', comment: 'ok' },
    )
  })
})
