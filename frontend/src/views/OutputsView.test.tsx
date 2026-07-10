import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const outputApiMock = vi.hoisted(() => ({
  list: vi.fn(),
  generate: vi.fn(),
  export: vi.fn(),
  delete: vi.fn(),
  archive: vi.fn(),
  restore: vi.fn(),
}))

vi.mock('../services/api', () => ({
  outputApi: outputApiMock,
}))

import { useStore } from '../store/useStore'
import OutputsView from './OutputsView'

const activeOutput = {
  output_id: 'out-active',
  kind: 'outline',
  title: 'Active Outline',
  content: 'Active content',
  source_doc_ids: ['doc-1'],
  status: 'active' as const,
  created_at: '2026-07-10T10:00:00',
  updated_at: '2026-07-10T10:00:00',
}

const archivedOutput = {
  output_id: 'out-archived',
  kind: 'outline',
  title: 'Archived Outline',
  content: 'Archived content',
  source_doc_ids: ['doc-1'],
  status: 'archived' as const,
  deleted_at: '2026-07-10T11:00:00',
  created_at: '2026-07-10T10:00:00',
  updated_at: '2026-07-10T11:00:00',
}

describe('OutputsView archived lifecycle', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useStore.setState({ selectedDocIds: [], toasts: [] })
    outputApiMock.list.mockImplementation((_kind?: string, includeArchived?: boolean) => Promise.resolve({
      outputs: includeArchived ? [archivedOutput] : [activeOutput],
      total: 1,
    }))
    outputApiMock.archive.mockResolvedValue({ message: 'archived' })
    outputApiMock.restore.mockResolvedValue({ message: 'restored' })
    outputApiMock.export.mockResolvedValue({
      filename: 'output.md',
      content_type: 'text/markdown',
      content: 'content',
    })
  })

  it('loads active outputs by default and archived outputs through an explicit filter', async () => {
    render(<OutputsView onModuleChange={vi.fn()} />)

    expect(await screen.findAllByText('Active Outline')).toHaveLength(2)
    expect(outputApiMock.list).toHaveBeenCalledWith(undefined, false)

    fireEvent.click(screen.getByRole('button', { name: 'Archived' }))

    await waitFor(() => expect(outputApiMock.list).toHaveBeenLastCalledWith(undefined, true))
    expect(await screen.findAllByText('Archived Outline')).toHaveLength(2)
    expect(screen.queryByText('Active Outline')).not.toBeInTheDocument()
  })

  it('archives active outputs and restores archived outputs from the detail toolbar', async () => {
    render(<OutputsView onModuleChange={vi.fn()} />)

    expect(await screen.findAllByText('Active Outline')).toHaveLength(2)
    fireEvent.click(screen.getByRole('button', { name: 'Archive output' }))
    await waitFor(() => expect(outputApiMock.archive).toHaveBeenCalledWith('out-active'))

    fireEvent.click(screen.getByRole('button', { name: 'Archived' }))
    expect(await screen.findAllByText('Archived Outline')).toHaveLength(2)
    fireEvent.click(screen.getByRole('button', { name: 'Restore output' }))

    await waitFor(() => expect(outputApiMock.restore).toHaveBeenCalledWith('out-archived'))
  })
})
