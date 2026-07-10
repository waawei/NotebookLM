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

  it('shows an error when the project list cannot be loaded', async () => {
    modelingApiMock.list.mockRejectedValue(new Error('offline'))
    render(<ModelingProjectsView />)

    expect(await screen.findByText('Unable to load modeling projects. Please try again.')).toBeInTheDocument()
  })
})
