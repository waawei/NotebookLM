import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import ModelingRuntimeStatus from './ModelingRuntimeStatus'

describe('ModelingRuntimeStatus', () => {
  it('shows each capability without blocking unrelated workflow actions', () => {
    render(<ModelingRuntimeStatus status={{
      workspace: { configured: true, writable: true },
      python: { available: true, version: '3.12.0' },
      git: { available: false, version: null },
      xelatex: { available: false, version: null },
    }} />)

    expect(screen.getByText('Workspace')).toBeInTheDocument()
    expect(screen.getByText('Python')).toBeInTheDocument()
    expect(screen.getByText('Git')).toBeInTheDocument()
    expect(screen.getByText('XeLaTeX')).toBeInTheDocument()
    expect(screen.getAllByText('Ready')).toHaveLength(2)
    expect(screen.getAllByText('Unavailable')).toHaveLength(2)
    expect(screen.getByText('3.12.0')).toBeInTheDocument()
  })
})
