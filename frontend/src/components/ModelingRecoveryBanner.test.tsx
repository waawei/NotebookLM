import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const modelingApiMock = vi.hoisted(() => ({ dismissRecovery: vi.fn() }))
vi.mock('../services/api', () => ({ modelingApi: modelingApiMock }))

import ModelingRecoveryBanner from './ModelingRecoveryBanner'

describe('ModelingRecoveryBanner', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    modelingApiMock.dismissRecovery.mockResolvedValue({ recovery_id: 'recovery-1' })
  })

  it('explains the safe recovery, links the interrupted run, and dismisses only the notice', async () => {
    const dismissed = vi.fn()
    render(<ModelingRecoveryBanner recovery={{
      recovery_id: 'recovery-1',
      project_id: 'project-1',
      from_state: 'experiment_running',
      to_state: 'experiment_implementation',
      interrupted_run_ids: ['exp-0001'],
      created_at: '2026-07-12T00:00:00',
    }} onDismissed={dismissed} />)

    expect(screen.getByText(/experiment_running/)).toBeInTheDocument()
    expect(screen.getByText(/experiment_implementation/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'exp-0001' })).toHaveAttribute('href', '#experiment-exp-0001')
    fireEvent.click(screen.getByRole('button', { name: 'Dismiss recovery notice' }))
    await waitFor(() => expect(modelingApiMock.dismissRecovery).toHaveBeenCalledWith('recovery-1'))
    expect(dismissed).toHaveBeenCalledWith('recovery-1')
  })
})
