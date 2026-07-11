import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import PaperWorkspace from './PaperWorkspace'

describe('PaperWorkspace', () => {
  it('shows editable markdown and review action', () => {
    render(<PaperWorkspace projectId="p-1" markdown="# Draft" latex="\\begin{document}x\\end{document}" onChanged={() => undefined} />)
    expect(screen.getByLabelText('Paper markdown')).toHaveValue('# Draft')
    expect(screen.getByRole('button', { name: 'Review' })).toBeEnabled()
  })

  it('disables only compilation when XeLaTeX is unavailable', () => {
    render(<PaperWorkspace projectId="p-1" markdown="# Draft" latex="\\begin{document}x\\end{document}" canCompile={false} onChanged={() => undefined} />)
    expect(screen.getByRole('button', { name: 'Save' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Review' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Compile' })).toBeDisabled()
  })
})
