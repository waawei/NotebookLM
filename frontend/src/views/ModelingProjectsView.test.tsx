import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const modelingApiMock = vi.hoisted(() => ({
  list: vi.fn(),
  create: vi.fn(),
  get: vi.fn(),
  advance: vi.fn(),
  rollback: vi.fn(),
}))

vi.mock('../services/api', () => ({ modelingApi: modelingApiMock }))

import ModelingProjectsView from './ModelingProjectsView'
import { useStore } from '../store/useStore'

const forecast = {
  project_id: 'project-1',
  name: 'Forecast',
  slug: 'forecast',
  workspace_path: 'C:/projects/forecast',
  state: 'project_initialized',
}

const workflowActionAvailability = [
  ['project_initialized', true, false],
  ['problem_parsing', true, true],
  ['data_profiling', true, true],
  ['model_planning', true, true],
  ['model_approval_pending', true, true],
  ['experiment_implementation', true, true],
  ['execution_approval_pending', true, true],
  ['experiment_running', true, true],
  ['result_validation', true, true],
  ['paper_drafting', true, true],
  ['consistency_review', true, true],
  ['final_approval_pending', true, true],
  ['packaging', true, true],
  ['commit_approval_pending', true, true],
  ['committing', true, true],
  ['completed', false, false],
] as const

describe('ModelingProjectsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    useStore.setState({ selectedModelingProjectId: null })
    modelingApiMock.list.mockResolvedValue({ projects: [forecast], total: 1 })
    modelingApiMock.get.mockResolvedValue(forecast)
    modelingApiMock.create.mockResolvedValue({ ...forecast, project_id: 'project-2', name: 'Churn', slug: 'churn' })
    modelingApiMock.advance.mockResolvedValue({ ...forecast, state: 'problem_parsing' })
    modelingApiMock.rollback.mockResolvedValue(forecast)
  })

  it('loads projects, selects one, and creates a project', async () => {
    render(<ModelingProjectsView />)

    expect(await screen.findByRole('heading', { name: 'Forecast' })).toBeInTheDocument()
    expect(screen.getAllByText('project_initialized')).not.toHaveLength(0)
    fireEvent.change(screen.getByLabelText('Project name'), { target: { value: 'Churn' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create project' }))

    await waitFor(() => expect(modelingApiMock.create).toHaveBeenCalledWith({ name: 'Churn' }))
    expect(await screen.findByRole('heading', { name: 'Churn' })).toBeInTheDocument()
    expect(useStore.getState().selectedModelingProjectId).toBe('project-2')
  })

  it('advances and rolls back the selected project with a reason', async () => {
    render(<ModelingProjectsView />)

    await screen.findByRole('heading', { name: 'Forecast' })
    fireEvent.click(screen.getByRole('button', { name: 'Advance project' }))
    await waitFor(() => expect(modelingApiMock.advance).toHaveBeenCalledWith('project-1'))
    await waitFor(() => expect(screen.getAllByText('problem_parsing')).not.toHaveLength(0))

    fireEvent.change(screen.getByLabelText('Rollback reason'), { target: { value: 'Need another pass' } })
    fireEvent.click(screen.getByRole('button', { name: 'Rollback project' }))
    await waitFor(() => expect(modelingApiMock.rollback).toHaveBeenCalledWith('project-1', 'Need another pass'))
  })

  it('disables rollback at project initialization while keeping advance usable', async () => {
    render(<ModelingProjectsView />)

    await screen.findByRole('heading', { name: 'Forecast' })
    expect(screen.getByRole('button', { name: 'Rollback project' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Advance project' })).toBeEnabled()

    fireEvent.click(screen.getByRole('button', { name: 'Advance project' }))
    await waitFor(() => expect(modelingApiMock.advance).toHaveBeenCalledWith('project-1'))
  })

  it('disables all illegal actions at completion', async () => {
    modelingApiMock.list.mockResolvedValue({ projects: [{ ...forecast, state: 'completed' }], total: 1 })
    render(<ModelingProjectsView />)

    await screen.findByRole('heading', { name: 'Forecast' })
    expect(screen.getByRole('button', { name: 'Advance project' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Rollback project' })).toBeDisabled()
  })

  it('keeps both legal actions usable in problem parsing', async () => {
    modelingApiMock.list.mockResolvedValue({ projects: [{ ...forecast, state: 'problem_parsing' }], total: 1 })
    render(<ModelingProjectsView />)

    await screen.findByRole('heading', { name: 'Forecast' })
    expect(screen.getByRole('button', { name: 'Advance project' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Rollback project' })).toBeEnabled()

    fireEvent.click(screen.getByRole('button', { name: 'Rollback project' }))
    await waitFor(() => expect(modelingApiMock.rollback).toHaveBeenCalledWith('project-1', ''))
  })

  it.each(workflowActionAvailability)(
    'matches backend action availability for %s',
    async (state, advanceEnabled, rollbackEnabled) => {
      modelingApiMock.list.mockResolvedValue({ projects: [{ ...forecast, state }], total: 1 })
      render(<ModelingProjectsView />)

      await screen.findByRole('heading', { name: 'Forecast' })
      const advance = screen.getByRole('button', { name: 'Advance project' })
      const rollback = screen.getByRole('button', { name: 'Rollback project' })
      expect(advance).toHaveProperty('disabled', !advanceEnabled)
      expect(rollback).toHaveProperty('disabled', !rollbackEnabled)
    },
  )

  it('shows an error when the project list cannot be loaded', async () => {
    modelingApiMock.list.mockRejectedValue(new Error('offline'))
    render(<ModelingProjectsView />)

    expect(await screen.findByText('Unable to load modeling projects. Please try again.')).toBeInTheDocument()
  })
})
