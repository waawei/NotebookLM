import { fireEvent, render, screen } from '@testing-library/react'
import { expect, test, vi } from 'vitest'
import ExperimentRunPanel from './ExperimentRunPanel'

test('offers execution only for prepared experiments', () => {
  const execute = vi.fn()
  render(<ExperimentRunPanel onExecute={execute} experiments={[{ experiment_id: 'exp-0001', project_id: 'p-1', config: { model: { kind: 'baseline' }, seed: 42, metrics: [] }, status: 'prepared' }]} />)
  fireEvent.click(screen.getByRole('button', { name: 'Run' }))
  expect(execute).toHaveBeenCalledWith('exp-0001')
})
