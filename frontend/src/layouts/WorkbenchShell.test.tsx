import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import WorkbenchShell from './WorkbenchShell'

describe('WorkbenchShell responsive panels', () => {
  it('keeps source selection and the inspector reachable on narrow screens', () => {
    render(
      <WorkbenchShell
        activeModule="workbench"
        title="Workbench"
        leftPanel={<div>Source selector</div>}
        centerPanel={<div>Conversation</div>}
        rightPanel={<div>Inspector content</div>}
        isDarkMode={false}
        onModuleChange={vi.fn()}
        onOpenUpload={vi.fn()}
        onOpenSearch={vi.fn()}
        onOpenExport={vi.fn()}
        onOpenNotes={vi.fn()}
        onOpenSettings={vi.fn()}
        onToggleDarkMode={vi.fn()}
      />,
    )

    expect(screen.getByLabelText('Open source selector')).toBeInTheDocument()
    expect(screen.getByLabelText('Open citation inspector')).toBeInTheDocument()
    expect(screen.getByTestId('mobile-source-panel')).toHaveClass('lg:hidden')
    expect(screen.getByTestId('mobile-inspector')).toHaveClass('xl:hidden')
  })
})
