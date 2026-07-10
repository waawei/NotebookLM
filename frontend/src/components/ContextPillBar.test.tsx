import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const wikiApiMock = vi.hoisted(() => ({
  list: vi.fn(),
}))

vi.mock('../services/api', () => ({
  wikiApi: wikiApiMock,
}))

import { useStore } from '../store/useStore'
import ContextPillBar from './ContextPillBar'

describe('ContextPillBar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    wikiApiMock.list.mockResolvedValue({
      pages: [
        {
          page_id: 'wiki-1',
          title: 'Retrieval Notes',
          content: '',
          source_doc_ids: [],
          created_at: '2026-07-10T10:00:00',
          updated_at: '2026-07-10T10:00:00',
        },
      ],
      total: 1,
    })
    useStore.setState({
      documents: [
        { doc_id: 'doc-1', filename: 'Research Brief.pdf', file_type: 'pdf', upload_time: '2026-07-10T00:00:00', status: 'completed', total_chunks: 3 },
      ],
      selectedDocIds: ['doc-1'],
      selectedWikiPageIds: ['wiki-1'],
    })
  })

  it('renders removable source and wiki context pills', async () => {
    render(<ContextPillBar />)

    expect(screen.getByText('Research Brief.pdf')).toBeInTheDocument()
    expect(await screen.findByText('Retrieval Notes')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Remove source Research Brief.pdf' }))
    expect(useStore.getState().selectedDocIds).toEqual([])

    fireEvent.click(screen.getByRole('button', { name: 'Remove wiki Retrieval Notes' }))
    expect(useStore.getState().selectedWikiPageIds).toEqual([])
  })

  it('renders a compact empty state when no context is selected', async () => {
    useStore.setState({ selectedDocIds: [], selectedWikiPageIds: [] })

    render(<ContextPillBar />)

    await waitFor(() => expect(wikiApiMock.list).toHaveBeenCalled())
    expect(screen.getByText('No context selected')).toBeInTheDocument()
  })
})
