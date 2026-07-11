import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const modelingApiMock = vi.hoisted(() => ({ decideApproval: vi.fn() }))
vi.mock('../services/api', () => ({ modelingApi: modelingApiMock }))

import ModelPlanApprovalCard from './ModelPlanApprovalCard'

const approval = {
  approval_id: 'approval-1',
  project_id: 'project-1',
  gate: 'model_approval',
  payload_hash: 'hash-1',
  payload: { artifact_id: 'plan-1', artifact_sha256: 'sha-1', version: 1 },
  status: 'pending',
}
const plan = {
  problem_summary: 'Forecast sales',
  candidates: [{
    name: 'Linear baseline',
    assumptions: ['stable relation'],
    features: ['category'],
    algorithm: 'linear regression',
    metrics: ['rmse'],
    risks: ['drift'],
  }],
}

describe('ModelPlanApprovalCard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    modelingApiMock.decideApproval.mockResolvedValue({ ...approval, decision: 'approved' })
  })

  it('renders candidates and approves the exact payload hash', async () => {
    const decided = vi.fn()
    render(<ModelPlanApprovalCard projectId="project-1" approval={approval} plan={plan} onDecided={decided} />)

    expect(screen.getByText('Linear baseline')).toBeInTheDocument()
    expect(screen.getByText(/drift/)).toBeInTheDocument()
    expect(screen.getByText(/hash-1/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Approve plan' }))

    await waitFor(() => expect(modelingApiMock.decideApproval).toHaveBeenCalledWith(
      'project-1',
      'approval-1',
      { decision: 'approved', payload_hash: 'hash-1', comment: '' },
    ))
    expect(decided).toHaveBeenCalled()
  })

  it('requires a non-empty comment before requesting changes', async () => {
    render(<ModelPlanApprovalCard projectId="project-1" approval={approval} plan={plan} onDecided={() => undefined} />)
    fireEvent.click(screen.getByRole('button', { name: 'Request changes' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Describe the requested changes.')
    expect(modelingApiMock.decideApproval).not.toHaveBeenCalled()

    fireEvent.change(screen.getByLabelText('Approval comment'), { target: { value: 'Revise assumptions' } })
    fireEvent.click(screen.getByRole('button', { name: 'Request changes' }))
    await waitFor(() => expect(modelingApiMock.decideApproval).toHaveBeenCalledWith(
      'project-1',
      'approval-1',
      { decision: 'changes_requested', payload_hash: 'hash-1', comment: 'Revise assumptions' },
    ))
  })
})
