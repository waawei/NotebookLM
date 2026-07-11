import { fireEvent, render, screen } from '@testing-library/react'
import { expect, test, vi } from 'vitest'
import ExperimentRunPanel from './ExperimentRunPanel'

test('offers execution only for prepared experiments', () => {
  const execute = vi.fn()
  const experiments = [{ experiment_id: 'exp-0001', project_id: 'p-1', config: { model: { kind: 'baseline' }, seed: 42, metrics: [] }, status: 'prepared' }]
  render(<ExperimentRunPanel projectId="p-1" onChanged={vi.fn()} onExecute={execute} experiments={experiments} />)
  fireEvent.click(screen.getByRole('button', { name: 'Run' }))
  expect(execute).toHaveBeenCalledWith('exp-0001')
})

test('disables execution when Python or the workspace is unavailable', () => {
  const experiments = [{ experiment_id: 'exp-0001', project_id: 'p-1', config: { model: { kind: 'baseline' }, seed: 42, metrics: [] }, status: 'prepared' }]
  render(<ExperimentRunPanel projectId="p-1" canExecute={false} onChanged={vi.fn()} onExecute={vi.fn()} experiments={experiments} />)
  expect(screen.getByRole('button', { name: 'Run' })).toBeDisabled()
})
