import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { modelingApi } from '../services/api'
import GitCommitApprovalCard from './GitCommitApprovalCard'
vi.mock('../services/api', () => ({ modelingApi: { requestCommit: vi.fn() } }))
describe('GitCommitApprovalCard', () => {
  it('submits exact reviewed paths and message', async () => { render(<GitCommitApprovalCard projectId="p-1" review={{ ok: true, paths: ['README.md'], diff: 'diff', issues: [] }} onChanged={() => undefined} />); fireEvent.change(screen.getByLabelText('Commit message'), { target: { value: 'feat: add modeling solution' } }); fireEvent.click(screen.getByRole('button', { name: 'Request commit approval' })); await waitFor(() => expect(modelingApi.requestCommit).toHaveBeenCalledWith('p-1', { paths: ['README.md'], commit_message: 'feat: add modeling solution' })) })

  it('disables only Git commands when Git is unavailable', () => {
    render(<GitCommitApprovalCard projectId="p-1" canCommit={false} review={{ ok: true, paths: ['README.md'], diff: 'diff', issues: [] }} onChanged={() => undefined} />)
    expect(screen.getByLabelText('Commit message')).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Refresh diff' })).toBeDisabled()
  })
})
