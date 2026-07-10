import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useStore } from '../store/useStore'
import ModuleNav from './ModuleNav'

describe('ModuleNav Reviva-style rail', () => {
  beforeEach(() => {
    useStore.setState({ language: 'en' })
  })

  it('uses a pale active state with a compact rail indicator', () => {
    render(<ModuleNav activeModule="workbench" onModuleChange={vi.fn()} />)

    const activeButton = screen.getByRole('button', { name: 'Workbench' })
    expect(activeButton).toHaveClass('bg-blue-50')
    expect(activeButton).not.toHaveClass('bg-blue-600')
    expect(screen.getByTestId('active-rail-indicator')).toBeInTheDocument()
  })

  it('includes the modeling workbench entry', () => {
    render(<ModuleNav activeModule="modeling" onModuleChange={vi.fn()} />)

    expect(screen.getByRole('button', { name: 'Modeling' })).toHaveAttribute('aria-current', 'page')
  })

  it('uses Chinese module labels when the language preference is Chinese', () => {
    useStore.setState({ language: 'zh-CN' })

    render(<ModuleNav activeModule="workbench" onModuleChange={vi.fn()} />)

    expect(screen.getByRole('button', { name: '工作台' })).toBeInTheDocument()
  })
})
