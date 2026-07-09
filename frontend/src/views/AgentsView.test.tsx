import { act, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const agentsApiMock = vi.hoisted(() => ({
  listRuns: vi.fn(),
  getRun: vi.fn(),
}))

vi.mock('../services/api', () => ({
  agentsApi: agentsApiMock,
}))

import AgentsView from './AgentsView'

const runningRun = {
  run_id: 'run-1',
  skill_id: 'paper_planner',
  status: 'running' as const,
  input_payload: { doc_ids: ['doc-1'] },
  output_id: null,
  error: null,
  steps: [],
}

const completedRun = {
  ...runningRun,
  status: 'completed' as const,
  output_id: 'output-1',
  steps: [{ step_id: 'step-1', step_index: 0, kind: 'generation', title: 'Generated output', payload: {}, created_at: 'now' }],
}

describe('AgentsView', () => {
  let scheduledPoll: (() => void) | undefined

  beforeEach(() => {
    vi.clearAllMocks()
    agentsApiMock.listRuns.mockResolvedValue({ runs: [runningRun], total: 1 })
    agentsApiMock.getRun.mockResolvedValue(completedRun)
    const nativeSetInterval = window.setInterval.bind(window)
    vi.spyOn(window, 'setInterval').mockImplementation((handler, timeout, ...args) => {
      if (timeout === 1500) scheduledPoll = handler as () => void
      return nativeSetInterval(handler, timeout, ...args)
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('polls active runs every 1500ms and exposes a persisted output link', async () => {
    render(<AgentsView onOpenOutput={vi.fn()} />)
    await screen.findByText('paper_planner')

    await waitFor(() => expect(window.setInterval).toHaveBeenCalledWith(expect.any(Function), 1500))
    await act(async () => { scheduledPoll?.() })

    await waitFor(() => expect(agentsApiMock.getRun).toHaveBeenCalledWith('run-1'))
    expect(screen.getByRole('link', { name: 'Open output' })).toHaveAttribute('href', '#outputs')
    expect(screen.getByText('Generated output')).toBeInTheDocument()
  })
})
