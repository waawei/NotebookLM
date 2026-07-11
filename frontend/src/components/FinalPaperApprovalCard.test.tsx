import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { modelingApi } from '../services/api'
import FinalPaperApprovalCard from './FinalPaperApprovalCard'

vi.mock('../services/api', () => ({ modelingApi: { requestFinalApproval: vi.fn() } }))

describe('FinalPaperApprovalCard', () => {
  it('disables final approval for blocking review', () => {
    render(<FinalPaperApprovalCard projectId="p-1" review={{ status: 'failed', issues: [{ severity: 'blocking', code: 'missing', message: 'Missing metric', location: 'Results', artifact_ids: [] }] }} onChanged={() => undefined} />)
    expect(screen.getByRole('button', { name: 'Request final approval' })).toBeDisabled()
  })

  it('requests final approval after a passed review', async () => {
    render(<FinalPaperApprovalCard projectId="p-1" review={{ status: 'passed', issues: [] }} onChanged={() => undefined} />)

    fireEvent.click(screen.getByRole('button', { name: 'Request final approval' }))

    await waitFor(() => expect(modelingApi.requestFinalApproval).toHaveBeenCalledWith('p-1'))
  })
})
