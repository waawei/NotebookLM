import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { modelingApi } from '../services/api'
import GitCommitApprovalCard from './GitCommitApprovalCard'
vi.mock('../services/api', () => ({ modelingApi: { requestCommit: vi.fn() } }))
describe('GitCommitApprovalCard', () => {
  it('submits exact reviewed paths and message', async () => { render(<GitCommitApprovalCard projectId="p-1" review={{ ok: true, paths: ['README.md'], diff: 'diff', diff_hash: 'diff-hash', issues: [] }} onChanged={() => undefined} />); fireEvent.change(screen.getByLabelText('Commit message'), { target: { value: 'feat: add modeling solution' } }); fireEvent.click(screen.getByRole('button', { name: 'Request commit approval' })); await waitFor(() => expect(modelingApi.requestCommit).toHaveBeenCalledWith('p-1', { paths: ['README.md'], commit_message: 'feat: add modeling solution' })) })

  it('disables only Git commands when Git is unavailable', () => {
    render(<GitCommitApprovalCard projectId="p-1" canCommit={false} review={{ ok: true, paths: ['README.md'], diff: 'diff', diff_hash: 'diff-hash', issues: [] }} onChanged={() => undefined} />)
    expect(screen.getByLabelText('Commit message')).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Refresh diff' })).toBeDisabled()
  })

  it('resumes a persisted approved request using its approved message', () => {
    render(<GitCommitApprovalCard projectId="p-1" review={{ ok: true, paths: ['README.md'], diff: 'diff', diff_hash: 'diff-hash', issues: [] }} approval={{ approval_id: 'approval-1', payload_hash: 'hash-1', status: 'approved', payload: { paths: ['README.md'], diff_hash: 'diff-hash', commit_message: 'feat: add modeling solution' } }} onChanged={() => undefined} />)
    expect(screen.getByLabelText('Commit message')).toHaveValue('feat: add modeling solution')
    expect(screen.getByRole('button', { name: 'Commit approved files' })).toBeEnabled()
  })

  it('removes an approved commit action when the reviewed diff is stale', () => {
    render(<GitCommitApprovalCard projectId="p-1" review={{ ok: true, paths: ['README.md'], diff: 'changed', diff_hash: 'new-diff', issues: [] }} approval={{ approval_id: 'approval-1', payload_hash: 'hash-1', status: 'approved', payload: { paths: ['README.md'], diff_hash: 'old-diff', commit_message: 'feat: add modeling solution' } }} onChanged={() => undefined} />)
    expect(screen.queryByRole('button', { name: 'Commit approved files' })).not.toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('Approval does not match')
  })
})
