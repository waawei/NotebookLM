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

import { settingsApi } from './api'

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
})
