import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const documentApiMock = vi.hoisted(() => ({ search: vi.fn(), delete: vi.fn() }))
const spacesApiMock = vi.hoisted(() => ({ list: vi.fn() }))

vi.mock('../services/api', () => ({
  documentApi: documentApiMock,
  spacesApi: spacesApiMock,
}))

import Sidebar from './Sidebar'
import { useStore } from '../store/useStore'

describe('Sidebar document status', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    documentApiMock.search.mockImplementation(() => new Promise(() => {}))
    spacesApiMock.list.mockImplementation(() => new Promise(() => {}))
    useStore.setState({
      documents: [
        { doc_id: 'indexed', filename: 'indexed.pdf', file_type: 'pdf', upload_time: '2026-07-10T00:00:00', status: 'completed', total_chunks: 2, summary_status: 'unavailable', summary_error: 'LLM summary unavailable' },
        { doc_id: 'failed', filename: 'failed.pdf', file_type: 'pdf', upload_time: '2026-07-10T00:00:00', status: 'failed', total_chunks: 0, summary_status: 'pending' },
      ],
      selectedDocIds: ['indexed'],
      activeSpaceId: null,
    })
  })

  it('shows indexed summary unavailability separately from processing failure', () => {
    render(<Sidebar isCollapsed={false} onToggle={vi.fn()} onUploadClick={vi.fn()} />)

    expect(screen.getByText('LLM summary unavailable')).toBeInTheDocument()
    expect(screen.getByText('Processing failed')).toBeInTheDocument()
    expect(screen.getByText('Selected')).toBeInTheDocument()
  })

  it('uses a neutral Reviva-style context panel with pale selected sources', () => {
    render(<Sidebar isCollapsed={false} onToggle={vi.fn()} onUploadClick={vi.fn()} />)

    expect(screen.getByTestId('sources-sidebar')).toHaveClass('bg-[#f1f0ef]')
    expect(screen.getByRole('button', { name: /Add source/i })).toHaveClass('bg-blue-600')

    const selectedCard = screen.getByText('indexed.pdf').closest('[data-testid="source-card"]')
    expect(selectedCard).toHaveClass('bg-blue-50')
    expect(selectedCard).not.toHaveClass('bg-blue-600')
  })

  it('uses a quiet empty source state without a blue gradient block', () => {
    useStore.setState({ documents: [], selectedDocIds: [] })

    render(<Sidebar isCollapsed={false} onToggle={vi.fn()} onUploadClick={vi.fn()} />)

    expect(screen.getByTestId('empty-source-icon')).toHaveClass('bg-blue-50')
    expect(screen.getByTestId('empty-source-icon')).not.toHaveClass('bg-gradient-to-br')
  })
})
