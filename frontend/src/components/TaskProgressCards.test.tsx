import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const agentsApiMock = vi.hoisted(() => ({
  listRuns: vi.fn(),
}))

vi.mock('../services/api', () => ({
  agentsApi: agentsApiMock,
}))

import { useStore } from '../store/useStore'
import TaskProgressCards from './TaskProgressCards'

describe('TaskProgressCards', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useStore.setState({ previewTarget: null, activeModule: 'workbench' })
    agentsApiMock.listRuns.mockResolvedValue({
      runs: [
        {
          run_id: 'run-1',
          skill_id: 'paper_planner',
          status: 'running',
          input_payload: { request: 'outline' },
          output_id: null,
          error: null,
          steps: [],
        },
        {
          run_id: 'run-2',
          skill_id: 'quiz_builder',
          status: 'completed',
          input_payload: { request: 'quiz' },
          output_id: 'out-1',
          error: null,
          steps: [{ step_id: 'step-1', step_index: 0, kind: 'generation', title: 'Generated output', payload: {}, created_at: 'now' }],
        },
        {
          run_id: 'run-3',
          skill_id: 'brief_writer',
          status: 'failed',
          input_payload: { request: 'brief' },
          output_id: null,
          error: 'Tool failed safely',
          steps: [],
        },
      ],
      total: 3,
    })
  })

  it('renders running, completed, and failed persisted task cards', async () => {
    render(<TaskProgressCards />)

    expect(await screen.findByText('paper_planner')).toBeInTheDocument()
    expect(screen.getByText('Running')).toBeInTheDocument()
    expect(screen.getByText('Completed')).toBeInTheDocument()
    expect(screen.getByText('Failed')).toBeInTheDocument()
    expect(screen.getByText('Tool failed safely')).toBeInTheDocument()

    const card = screen.getByTestId('task-card-run-2')
    expect(card).toHaveClass('bg-white')
    expect(card).toHaveClass('border-[#e2e1de]')
  })

  it('opens completed output artifacts and exposes the run list', async () => {
    render(<TaskProgressCards />)

    fireEvent.click(await screen.findByRole('button', { name: 'Open artifact for quiz_builder' }))

    expect(useStore.getState().previewTarget).toEqual({
      type: 'output',
      id: 'out-1',
      title: 'quiz_builder output',
    })

    fireEvent.click(screen.getByRole('button', { name: 'View run paper_planner' }))
    expect(useStore.getState().activeModule).toBe('agents')
  })
})
