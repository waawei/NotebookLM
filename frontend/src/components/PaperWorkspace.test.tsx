import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import PaperWorkspace from './PaperWorkspace'

const modelingApiMock = vi.hoisted(() => ({ listPaperReviews: vi.fn() }))
vi.mock('../services/api', () => ({ modelingApi: modelingApiMock }))

describe('PaperWorkspace', () => {
  beforeEach(() => {
    modelingApiMock.listPaperReviews.mockResolvedValue({ reviews: [], total: 0 })
  })
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

  it('disables review when the workspace is unavailable', () => {
    render(<PaperWorkspace projectId="p-1" markdown="# Draft" latex="\\begin{document}x\\end{document}" canWrite={false} canReview={false} onChanged={() => undefined} />)

    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Review' })).toBeDisabled()
  })

  it('restores a passed review so a persisted final approval can be decided', async () => {
    modelingApiMock.listPaperReviews.mockResolvedValue({ reviews: [{ status: 'passed', issues: [] }], total: 1 })
    render(<PaperWorkspace projectId="p-1" markdown="# Draft" latex="\\begin{document}x\\end{document}" approval={{ approval_id: 'approval-1', project_id: 'p-1', gate: 'final_approval', payload_hash: 'hash', payload: {}, status: 'pending' }} onChanged={() => undefined} />)

    await waitFor(() => expect(screen.getByRole('button', { name: 'Approve final paper' })).toBeEnabled())
  })
})
