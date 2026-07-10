import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { OutputItem } from '../services/api'
import ArtifactLifecycleMenu from './ArtifactLifecycleMenu'

const activeOutput: OutputItem = {
  output_id: 'out-1',
  kind: 'outline',
  title: 'Chapter 2 Outline',
  content: 'Outline content',
  source_doc_ids: ['doc-1'],
  status: 'active',
  created_at: '2026-07-10T10:00:00',
  updated_at: '2026-07-10T10:00:00',
}

describe('ArtifactLifecycleMenu', () => {
  it('offers preview, export, and archive actions for active artifacts', () => {
    const onPreview = vi.fn()
    const onExport = vi.fn()
    const onArchive = vi.fn()

    render(
      <ArtifactLifecycleMenu
        output={activeOutput}
        onPreview={onPreview}
        onExport={onExport}
        onArchive={onArchive}
        onRestore={vi.fn()}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Artifact actions for Chapter 2 Outline' }))
    fireEvent.click(screen.getByRole('menuitem', { name: 'Preview' }))
    fireEvent.click(screen.getByRole('button', { name: 'Artifact actions for Chapter 2 Outline' }))
    fireEvent.click(screen.getByRole('menuitem', { name: 'Export' }))
    fireEvent.click(screen.getByRole('button', { name: 'Artifact actions for Chapter 2 Outline' }))
    fireEvent.click(screen.getByRole('menuitem', { name: 'Archive' }))

    expect(onPreview).toHaveBeenCalledTimes(1)
    expect(onExport).toHaveBeenCalledTimes(1)
    expect(onArchive).toHaveBeenCalledTimes(1)
  })

  it('offers restore instead of archive for archived artifacts', () => {
    const onRestore = vi.fn()

    render(
      <ArtifactLifecycleMenu
        output={{ ...activeOutput, status: 'archived' }}
        onPreview={vi.fn()}
        onExport={vi.fn()}
        onArchive={vi.fn()}
        onRestore={onRestore}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Artifact actions for Chapter 2 Outline' }))

    expect(screen.queryByRole('menuitem', { name: 'Archive' })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('menuitem', { name: 'Restore' }))
    expect(onRestore).toHaveBeenCalledTimes(1)
  })
})
