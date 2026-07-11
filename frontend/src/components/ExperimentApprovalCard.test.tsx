import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { expect, test, vi } from 'vitest'
import ExperimentApprovalCard from './ExperimentApprovalCard'
import { modelingApi } from '../services/api'

vi.mock('../services/api', async () => ({ ...(await vi.importActual('../services/api')), modelingApi: { decideApproval: vi.fn().mockResolvedValue({}) } }))

test('shows execution content and approves exact hash', async () => {
  render(<ExperimentApprovalCard projectId="p-1" approval={{ approval_id: 'a-1', project_id: 'p-1', gate: 'execution_approval', payload_hash: 'hash', payload: {}, status: 'pending' }} batch={{ experiment_id: 'exp-0001', commands: [['python', 'src/train.py']], timeout_seconds: 60, max_output_bytes: 1024, network_allowed: false, code_hash: 'code', input_hashes: {}, source_hashes: {}, dependency_lock: 'numpy==1.26.4', dependency_diff: ['+ numpy==1.26.4'] }} onDecided={vi.fn()} />)
  expect(screen.getByText(/Code hash: code/)).toBeInTheDocument()
  expect(screen.getByText(/Inputs: no registered inputs/)).toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Approve execution' }))
  await waitFor(() => expect(vi.mocked(modelingApi.decideApproval)).toHaveBeenCalled())
})

test('disables execution approval when the workspace is unavailable', () => {
  render(<ExperimentApprovalCard projectId="p-1" canDecide={false} approval={{ approval_id: 'a-1', project_id: 'p-1', gate: 'execution_approval', payload_hash: 'hash', payload: {}, status: 'pending' }} batch={{ experiment_id: 'exp-0001', commands: [['python', 'src/train.py']], timeout_seconds: 60, max_output_bytes: 1024, network_allowed: false, code_hash: 'code', input_hashes: {}, source_hashes: {}, dependency_lock: '', dependency_diff: [] }} onDecided={vi.fn()} />)

  expect(screen.getByRole('button', { name: 'Approve execution' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Request changes' })).toBeDisabled()
})
