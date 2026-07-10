import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const previewApiMock = vi.hoisted(() => ({
  get: vi.fn(),
}))

vi.mock('../services/api', () => ({
  previewApi: previewApiMock,
}))

import { useStore } from '../store/useStore'
import PreviewPane from './PreviewPane'

describe('PreviewPane', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useStore.setState({ previewTarget: null })
  })

  it('renders an empty preview state', () => {
    render(<PreviewPane />)

    expect(screen.getByTestId('preview-pane')).toBeInTheDocument()
    expect(screen.getByText('Select an item to preview')).toBeInTheDocument()
  })

  it('renders loading and loaded preview states without raw html', async () => {
    previewApiMock.get.mockResolvedValue({
      type: 'wiki',
      id: 'wiki-1',
      title: 'Retrieval Notes',
      content_preview: '<b># Retrieval</b>\nBounded content.',
      metadata: { source_count: 1, updated_at: '2026-07-10T10:00:00' },
      links: [{ type: 'document', id: 'doc-1', title: 'Research Brief.pdf' }],
    })
    useStore.setState({ previewTarget: { type: 'wiki', id: 'wiki-1', title: 'Retrieval Notes' } })

    render(<PreviewPane />)

    expect(screen.getByText('Loading preview')).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'Retrieval Notes' })).toBeInTheDocument()
    expect(screen.getByTestId('preview-content')).toHaveTextContent('<b># Retrieval</b>')
    expect(screen.getByText('source_count')).toBeInTheDocument()
    expect(screen.getByText('Research Brief.pdf')).toBeInTheDocument()
    expect(screen.getByTestId('preview-content')).toHaveClass('overflow-y-auto')
  })

  it('renders an error state with retry', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
    previewApiMock.get
      .mockRejectedValueOnce(new Error('preview failed'))
      .mockResolvedValueOnce({
        type: 'output',
        id: 'out-1',
        title: 'Recovered Output',
        content_preview: 'Recovered content.',
        metadata: { kind: 'outline' },
        links: [],
      })
    useStore.setState({ previewTarget: { type: 'output', id: 'out-1', title: 'Output' } })

    render(<PreviewPane />)

    expect(await screen.findByText('Preview unavailable')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Retry preview' }))

    await waitFor(() => expect(previewApiMock.get).toHaveBeenCalledTimes(2))
    expect(await screen.findByRole('heading', { name: 'Recovered Output' })).toBeInTheDocument()
    consoleError.mockRestore()
  })
})
