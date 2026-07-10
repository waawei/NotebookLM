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

import { chatApi, outputApi, previewApi, settingsApi } from './api'

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
