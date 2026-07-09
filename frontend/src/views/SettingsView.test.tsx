import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const settingsApiMock = vi.hoisted(() => ({
  getStatus: vi.fn(),
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
  warnings: [],
}

describe('SettingsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    settingsApiMock.getStatus.mockResolvedValue(safeStatus)
    settingsApiMock.save.mockResolvedValue({ ...safeStatus, api_key_configured: true })
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
})
