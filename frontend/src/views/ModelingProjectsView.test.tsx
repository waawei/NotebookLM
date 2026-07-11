import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const modelingApiMock = vi.hoisted(() => ({
  list: vi.fn(),
  create: vi.fn(),
  get: vi.fn(),
  advance: vi.fn(),
  rollback: vi.fn(),
  listArtifacts: vi.fn(),
  getArtifact: vi.fn(),
  listApprovals: vi.fn(),
  parseProblem: vi.fn(),
  profileData: vi.fn(),
  createModelPlan: vi.fn(),
  uploadInput: vi.fn(),
  decideApproval: vi.fn(),
  checkDeliverables: vi.fn(),
  buildDeliverables: vi.fn(),
  gitStatus: vi.fn(),
  reviewGit: vi.fn(),
  requestCommit: vi.fn(),
  commit: vi.fn(),
  runtime: vi.fn(),
  recoveries: vi.fn(),
  dismissRecovery: vi.fn(),
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
    modelingApiMock.listArtifacts.mockResolvedValue({ artifacts: [], total: 0 })
    modelingApiMock.listApprovals.mockResolvedValue({ approvals: [], total: 0 })
    modelingApiMock.parseProblem.mockResolvedValue({})
    modelingApiMock.profileData.mockResolvedValue({})
    modelingApiMock.createModelPlan.mockResolvedValue({})
    modelingApiMock.getArtifact.mockResolvedValue({})
    modelingApiMock.checkDeliverables.mockResolvedValue({ ok: false, issues: [] })
    modelingApiMock.gitStatus.mockResolvedValue({ paths: [] })
    modelingApiMock.runtime.mockResolvedValue({
      workspace: { configured: true, writable: true },
      python: { available: true, version: '3.12.0' },
      git: { available: true, version: 'git version 2.45.0' },
      xelatex: { available: true, version: 'XeLaTeX' },
    })
    modelingApiMock.recoveries.mockResolvedValue({ recoveries: [], total: 0 })
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
    expect(screen.queryByText('Competition inputs')).not.toBeInTheDocument()
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

  it.each([
    ['problem_parsing', 'Parse problem', 'parseProblem', undefined],
    ['data_profiling', 'Profile data', 'profileData', 'data-1'],
    ['model_planning', 'Create model plan', 'createModelPlan', undefined],
  ] as const)('runs the legal Phase 2 action for %s', async (state, label, method, artifactId) => {
    modelingApiMock.list.mockResolvedValue({ projects: [{ ...forecast, state }], total: 1 })
    modelingApiMock.listArtifacts.mockResolvedValue({
      artifacts: artifactId ? [{ artifact_id: artifactId, artifact_type: 'data_input' }] : [],
      total: artifactId ? 1 : 0,
    })
    render(<ModelingProjectsView />)

    await screen.findByRole('heading', { name: 'Forecast' })
    fireEvent.click(await screen.findByRole('button', { name: label }))
    await waitFor(() => {
      if (artifactId) expect(modelingApiMock[method]).toHaveBeenCalledWith('project-1', artifactId)
      else expect(modelingApiMock[method]).toHaveBeenCalledWith('project-1')
    })
  })

  it('loads the pending plan and renders its approval card', async () => {
    modelingApiMock.list.mockResolvedValue({ projects: [{ ...forecast, state: 'model_approval_pending' }], total: 1 })
    modelingApiMock.listArtifacts.mockResolvedValue({
      artifacts: [{ artifact_id: 'plan-1', artifact_type: 'model_plan' }],
      total: 1,
    })
    modelingApiMock.listApprovals.mockResolvedValue({
      approvals: [{
        approval_id: 'approval-1',
        project_id: 'project-1',
        gate: 'model_approval',
        payload_hash: 'hash-1',
        payload: { artifact_id: 'plan-1', artifact_sha256: 'sha-1', version: 1 },
        status: 'pending',
      }],
      total: 1,
    })
    modelingApiMock.getArtifact.mockResolvedValue({
      artifact_id: 'plan-1',
      content: {
        problem_summary: 'Forecast sales',
        candidates: [{ name: 'Linear baseline', assumptions: [], features: [], algorithm: 'linear', metrics: ['rmse'], risks: ['drift'] }],
      },
    })

    render(<ModelingProjectsView />)

    expect(await screen.findByText('Model plan approval')).toBeInTheDocument()
    expect(screen.getByText('Linear baseline')).toBeInTheDocument()
  })

  it('selects the newest pending model approval', async () => {
    modelingApiMock.list.mockResolvedValue({ projects: [{ ...forecast, state: 'model_approval_pending' }], total: 1 })
    modelingApiMock.listArtifacts.mockResolvedValue({ artifacts: [], total: 0 })
    modelingApiMock.listApprovals.mockResolvedValue({
      approvals: [
        { approval_id: 'old', project_id: 'project-1', gate: 'model_approval', payload_hash: 'old-hash', payload: { artifact_id: 'old-plan', artifact_sha256: 'old-sha', version: 1 }, status: 'pending', created_at: '2026-07-11T01:00:00' },
        { approval_id: 'new', project_id: 'project-1', gate: 'model_approval', payload_hash: 'new-hash', payload: { artifact_id: 'new-plan', artifact_sha256: 'new-sha', version: 2 }, status: 'pending', created_at: '2026-07-11T02:00:00' },
      ],
      total: 2,
    })
    modelingApiMock.getArtifact.mockResolvedValue({
      artifact_id: 'new-plan',
      content: { problem_summary: 'Newest', candidates: [] },
    })

    render(<ModelingProjectsView />)

    await screen.findByText('Model plan approval')
    expect(modelingApiMock.getArtifact).toHaveBeenCalledWith('project-1', 'new-plan')
    expect(screen.getByText(/new-sha/)).toBeInTheDocument()
  })

  it('ignores an out-of-order evidence response from the previous project', async () => {
    let resolveFirst: (value: unknown) => void = () => undefined
    const firstArtifacts = new Promise((resolve) => { resolveFirst = resolve })
    const second = { ...forecast, project_id: 'project-2', name: 'Second', slug: 'second' }
    modelingApiMock.list.mockResolvedValue({ projects: [forecast, second], total: 2 })
    modelingApiMock.listArtifacts
      .mockReturnValueOnce(firstArtifacts)
      .mockResolvedValueOnce({ artifacts: [{ artifact_id: 'second-artifact', artifact_type: 'data_input', relative_path: 'data/raw/second.csv' }], total: 1 })
    modelingApiMock.listApprovals.mockResolvedValue({ approvals: [], total: 0 })
    render(<ModelingProjectsView />)

    await screen.findByRole('heading', { name: 'Forecast' })
    fireEvent.click(screen.getByRole('button', { name: /Second/ }))
    expect(await screen.findByRole('heading', { name: 'Second' })).toBeInTheDocument()
    expect(await screen.findByText(/second.csv/)).toBeInTheDocument()
    resolveFirst({ artifacts: [{ artifact_id: 'old-artifact', artifact_type: 'data_input', relative_path: 'data/raw/old.csv' }], total: 1 })

    await waitFor(() => expect(screen.queryByText(/old.csv/)).not.toBeInTheDocument())
    expect(screen.getByText(/second.csv/)).toBeInTheDocument()
  })

  it('does not render the previous project approval while new evidence loads', async () => {
    let resolveSecond: (value: unknown) => void = () => undefined
    const secondArtifacts = new Promise((resolve) => { resolveSecond = resolve })
    const second = { ...forecast, project_id: 'project-2', name: 'Second', slug: 'second', state: 'model_approval_pending' }
    modelingApiMock.list.mockResolvedValue({ projects: [{ ...forecast, state: 'model_approval_pending' }, second], total: 2 })
    modelingApiMock.listArtifacts
      .mockResolvedValueOnce({ artifacts: [], total: 0 })
      .mockReturnValueOnce(secondArtifacts)
    modelingApiMock.listApprovals.mockResolvedValueOnce({
      approvals: [{ approval_id: 'old', project_id: 'project-1', gate: 'model_approval', payload_hash: 'old-hash', payload: { artifact_id: 'old-plan', artifact_sha256: 'old-sha', version: 1 }, status: 'pending' }],
      total: 1,
    }).mockResolvedValueOnce({ approvals: [], total: 0 })
    modelingApiMock.getArtifact.mockResolvedValueOnce({
      artifact_id: 'old-plan',
      content: { problem_summary: 'Old plan', candidates: [] },
    })
    render(<ModelingProjectsView />)

    expect(await screen.findByText('Model plan approval')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Second/ }))
    expect(await screen.findByRole('heading', { name: 'Second' })).toBeInTheDocument()
    await waitFor(() => expect(screen.queryByText('Model plan approval')).not.toBeInTheDocument())
    await act(async () => {
      resolveSecond({ artifacts: [], total: 0 })
    })
  })
})
