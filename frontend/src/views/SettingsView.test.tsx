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
})
