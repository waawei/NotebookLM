import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { act } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const outputApiMock = vi.hoisted(() => ({
  list: vi.fn(),
  export: vi.fn(),
  archive: vi.fn(),
  restore: vi.fn(),
}))

vi.mock('../services/api', () => ({
  outputApi: outputApiMock,
}))

import { useStore } from '../store/useStore'
import ArtifactList from './ArtifactList'

describe('ArtifactList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useStore.setState({ artifactRefreshToken: 0, previewTarget: null })
    outputApiMock.export.mockResolvedValue({
      filename: 'chapter-2-outline.md',
      content_type: 'text/markdown',
      content: 'Outline content',
    })
    outputApiMock.archive.mockResolvedValue({ message: 'archived' })
    outputApiMock.restore.mockResolvedValue({ message: 'restored' })
  })

  it('renders persisted outputs as compact artifact cards', async () => {
    outputApiMock.list.mockResolvedValue({
      outputs: [
        {
          output_id: 'out-1',
          kind: 'outline',
          title: 'Chapter 2 Outline',
          content: 'Outline content',
          source_doc_ids: ['doc-1', 'doc-2'],
          created_at: '2026-07-10T10:00:00',
          updated_at: '2026-07-10T10:00:00',
        },
      ],
      total: 1,
    })

    render(<ArtifactList />)

    expect(screen.getByTestId('artifact-list')).toBeInTheDocument()
    expect(await screen.findByText('Chapter 2 Outline')).toBeInTheDocument()
    expect(screen.getByText('outline')).toBeInTheDocument()
    expect(screen.getByText('2 sources')).toBeInTheDocument()
  })

  it('shows an empty persisted artifact state', async () => {
    outputApiMock.list.mockResolvedValue({ outputs: [], total: 0 })

    render(<ArtifactList />)

    expect(await screen.findByText('No artifacts yet')).toBeInTheDocument()
  })

  it('reloads when the artifact refresh token changes', async () => {
    outputApiMock.list.mockResolvedValue({ outputs: [], total: 0 })
    const { rerender } = render(<ArtifactList />)

    await waitFor(() => expect(outputApiMock.list).toHaveBeenCalledTimes(1))
    act(() => {
      useStore.setState({ artifactRefreshToken: 1 })
    })
    rerender(<ArtifactList />)

    await waitFor(() => expect(outputApiMock.list).toHaveBeenCalledTimes(2))
  })

  it('opens Preview for the selected output artifact', async () => {
    outputApiMock.list.mockResolvedValue({
      outputs: [
        {
          output_id: 'out-1',
          kind: 'outline',
          title: 'Chapter 2 Outline',
          content: 'Outline content',
          source_doc_ids: ['doc-1'],
          created_at: '2026-07-10T10:00:00',
          updated_at: '2026-07-10T10:00:00',
        },
      ],
      total: 1,
    })

    render(<ArtifactList />)

    fireEvent.click(await screen.findByRole('button', { name: 'Preview Chapter 2 Outline' }))

    expect(useStore.getState().previewTarget).toEqual({
      type: 'output',
      id: 'out-1',
      title: 'Chapter 2 Outline',
    })
  })

  it('exports and archives artifacts from the lifecycle menu', async () => {
    outputApiMock.list.mockResolvedValue({
      outputs: [
        {
          output_id: 'out-1',
          kind: 'outline',
          title: 'Chapter 2 Outline',
          content: 'Outline content',
          source_doc_ids: ['doc-1'],
          status: 'active',
          created_at: '2026-07-10T10:00:00',
          updated_at: '2026-07-10T10:00:00',
        },
      ],
      total: 1,
    })

    render(<ArtifactList />)

    fireEvent.click(await screen.findByRole('button', { name: 'Artifact actions for Chapter 2 Outline' }))
    fireEvent.click(screen.getByRole('menuitem', { name: 'Export' }))
    await waitFor(() => expect(outputApiMock.export).toHaveBeenCalledWith('out-1'))

    fireEvent.click(screen.getByRole('button', { name: 'Artifact actions for Chapter 2 Outline' }))
    fireEvent.click(screen.getByRole('menuitem', { name: 'Archive' }))
    await waitFor(() => expect(outputApiMock.archive).toHaveBeenCalledWith('out-1'))
    expect(useStore.getState().artifactRefreshToken).toBe(1)
  })

  it('restores archived artifacts when the archived list is shown', async () => {
    outputApiMock.list.mockResolvedValue({
      outputs: [
        {
          output_id: 'out-1',
          kind: 'outline',
          title: 'Chapter 2 Outline',
          content: 'Outline content',
          source_doc_ids: ['doc-1'],
          status: 'archived',
          created_at: '2026-07-10T10:00:00',
          updated_at: '2026-07-10T10:00:00',
        },
      ],
      total: 1,
    })

    render(<ArtifactList includeArchived />)

    await waitFor(() => expect(outputApiMock.list).toHaveBeenCalledWith(undefined, true))
    fireEvent.click(await screen.findByRole('button', { name: 'Artifact actions for Chapter 2 Outline' }))
    fireEvent.click(screen.getByRole('menuitem', { name: 'Restore' }))

    await waitFor(() => expect(outputApiMock.restore).toHaveBeenCalledWith('out-1'))
  })
})
