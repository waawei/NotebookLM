import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const settingsApiMock = vi.hoisted(() => ({
  getStatus: vi.fn(),
  listModels: vi.fn(),
  save: vi.fn(),
  clear: vi.fn(),
  testLlm: vi.fn(),
}))

vi.mock('../services/api', () => ({
  settingsApi: settingsApiMock,
}))

import SettingsView from './SettingsView'

const safeStatus = {
  provider: 'openai',
  model: 'gpt-test',
  base_url_configured: false,
  api_key_configured: false,
  temperature: 0.7,
  max_tokens: 2000,
  top_k: 5,
  embedding_model: 'embedding-model',
  embedding_device: 'cpu',
  endpoint_mode: 'auto',
  warnings: [],
}

describe('SettingsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    settingsApiMock.getStatus.mockResolvedValue(safeStatus)
    settingsApiMock.save.mockResolvedValue({ ...safeStatus, api_key_configured: true })
    settingsApiMock.listModels.mockResolvedValue({ models: ['a-model'] })
  })

  it('submits but never renders a configured API key', async () => {
    render(<SettingsView />)
    await screen.findByText('Runtime settings')

    fireEvent.change(screen.getByLabelText('API key'), { target: { value: 'write-only-key' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save configuration' }))

    await waitFor(() => {
      expect(settingsApiMock.save).toHaveBeenCalledWith(
        expect.objectContaining({ api_key: 'write-only-key' }),
      )
    })
    expect(screen.queryByDisplayValue('write-only-key')).not.toBeInTheDocument()
    expect(screen.queryByText('write-only-key')).not.toBeInTheDocument()
  })

  it('uses the temporary typed key only for discovery and clears it afterwards', async () => {
    render(<SettingsView />)
    await screen.findByText('Runtime settings')

    fireEvent.change(screen.getByLabelText('API key'), { target: { value: 'temporary-browser-key' } })
    fireEvent.click(screen.getByRole('button', { name: 'Load available models' }))

    await waitFor(() => {
      expect(settingsApiMock.listModels).toHaveBeenCalledWith(
        expect.objectContaining({ api_key: 'temporary-browser-key' }),
      )
    })
    expect(screen.getByLabelText('API key')).toHaveValue('')
    expect(screen.getByLabelText('Model')).toHaveAttribute('list', 'available-models')
    expect(document.querySelector('#available-models option')).toHaveAttribute('value', 'a-model')
  })

  it('shows an API key only while the current field is toggled', async () => {
    render(<SettingsView />)
    await screen.findByText('Runtime settings')

    fireEvent.change(screen.getByLabelText('API key'), { target: { value: 'current-value' } })
    fireEvent.click(screen.getByRole('button', { name: 'Show API key' }))

    expect(screen.getByLabelText('API key')).toHaveAttribute('type', 'text')
  })

  it('renders a safe connection diagnostic and never writes it to storage', async () => {
    const diagnostic = {
      phase: 'chat_completion',
      status_code: 429,
      category: 'rate_limited',
      summary: 'The upstream request was rate limited.',
    }
    const setItem = vi.spyOn(Storage.prototype, 'setItem')
    settingsApiMock.testLlm.mockResolvedValue({
      ok: false,
      message: 'LLM connection failed. Check provider, model, endpoint, and API key.',
      diagnostic,
    })

    render(<SettingsView />)
    await screen.findByText('Runtime settings')
    fireEvent.click(screen.getByRole('button', { name: 'Test connection' }))

    expect(await screen.findByText('Connection details')).toBeInTheDocument()
    expect(screen.getByText('HTTP status')).toBeInTheDocument()
    expect(screen.getByText('429')).toBeInTheDocument()
    expect(screen.getByText(diagnostic.summary)).toBeInTheDocument()
    expect(setItem).not.toHaveBeenCalled()
    setItem.mockRestore()
  })

  it('clears connection details before a retry', async () => {
    const diagnostic = {
      phase: 'chat_completion',
      status_code: 429,
      category: 'rate_limited',
      summary: 'The upstream request was rate limited.',
    }
    settingsApiMock.testLlm
      .mockResolvedValueOnce({
        ok: false,
        message: 'LLM connection failed. Check provider, model, endpoint, and API key.',
        diagnostic,
      })
      .mockResolvedValueOnce({ ok: true, message: 'LLM connection succeeded' })

    render(<SettingsView />)
    await screen.findByText('Runtime settings')
    fireEvent.click(screen.getByRole('button', { name: 'Test connection' }))
    await screen.findByText('Connection details')
    fireEvent.click(screen.getByRole('button', { name: 'Test connection' }))

    await waitFor(() => {
      expect(screen.queryByText('Connection details')).not.toBeInTheDocument()
    })
  })

  it('tests the current Ollama form values without requiring a save first', async () => {
    settingsApiMock.testLlm.mockResolvedValue({
      ok: true,
      message: 'LLM connection succeeded',
    })

    render(<SettingsView />)
    await screen.findByText('Runtime settings')

    fireEvent.change(screen.getByLabelText('Provider'), { target: { value: 'ollama' } })
    fireEvent.click(screen.getByRole('button', { name: 'Test connection' }))

    await waitFor(() => {
      expect(settingsApiMock.testLlm).toHaveBeenCalledWith(
        expect.objectContaining({
          provider: 'ollama',
          model: 'qwen3:8b',
          base_url: 'http://localhost:11434',
          endpoint_mode: 'auto',
        }),
      )
    })
    expect(settingsApiMock.save).not.toHaveBeenCalled()
  })

  it('applies the Ollama preset and saves a local qwen model without a key', async () => {
    render(<SettingsView />)
    await screen.findByText('Runtime settings')

    fireEvent.change(screen.getByLabelText('Provider'), { target: { value: 'ollama' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save configuration' }))

    await waitFor(() => {
      expect(settingsApiMock.save).toHaveBeenCalledWith(
        expect.objectContaining({
          provider: 'ollama',
          model: 'qwen3:8b',
          base_url: 'http://localhost:11434',
          endpoint_mode: 'auto',
        }),
      )
    })
    expect(settingsApiMock.save).toHaveBeenCalledWith(expect.not.objectContaining({ api_key: expect.any(String) }))
  })

  it('applies the DeepSeek preset with an exact API base', async () => {
    render(<SettingsView />)
    await screen.findByText('Runtime settings')

    fireEvent.change(screen.getByLabelText('Provider'), { target: { value: 'deepseek' } })
    fireEvent.change(screen.getByLabelText('API key'), { target: { value: 'deepseek-secret' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save configuration' }))

    await waitFor(() => {
      expect(settingsApiMock.save).toHaveBeenCalledWith(
        expect.objectContaining({
          provider: 'deepseek',
          model: 'deepseek-v4-flash',
          base_url: 'https://api.deepseek.com',
          api_key: 'deepseek-secret',
          endpoint_mode: 'exact',
        }),
      )
    })
  })
})
