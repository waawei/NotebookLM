import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const modelingApiMock = vi.hoisted(() => ({
  list: vi.fn(), listArtifacts: vi.fn(), listApprovals: vi.fn(), listExperiments: vi.fn(),
  getArtifact: vi.fn(), runtime: vi.fn(), recoveries: vi.fn(), dismissRecovery: vi.fn(),
  advance: vi.fn(), rollback: vi.fn(), create: vi.fn(), parseProblem: vi.fn(), profileData: vi.fn(),
  createModelPlan: vi.fn(), prepareExperiment: vi.fn(), requestExecution: vi.fn(), executeExperiment: vi.fn(),
  gitStatus: vi.fn(), reviewGit: vi.fn(),
}))
vi.mock('../services/api', () => ({ modelingApi: modelingApiMock }))

import ModelingProjectsView from './ModelingProjectsView'
import { useStore } from '../store/useStore'

const project = { project_id: 'project-1', name: 'Fixture Forecast', slug: 'fixture-forecast', workspace_path: 'C:/workspace/fixture-forecast', state: 'model_approval_pending' }
const planApproval = { approval_id: 'model-approval', project_id: 'project-1', gate: 'model_approval', payload_hash: 'plan-hash', payload: { artifact_id: 'plan-1', artifact_sha256: 'plan-sha', version: 1 }, status: 'pending' }

describe('ModelingProjectsView workflow integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useStore.setState({ selectedModelingProjectId: null })
    modelingApiMock.list.mockResolvedValue({ projects: [project], total: 1 })
    modelingApiMock.listArtifacts.mockResolvedValue({ artifacts: [], total: 0 })
    modelingApiMock.listExperiments.mockResolvedValue({ experiments: [], total: 0 })
    modelingApiMock.listApprovals.mockResolvedValue({ approvals: [planApproval], total: 1 })
    modelingApiMock.getArtifact.mockResolvedValue({ artifact_id: 'plan-1', content: { problem_summary: 'Forecast sales', candidates: [] } })
    modelingApiMock.runtime.mockResolvedValue({ workspace: { configured: true, writable: true }, python: { available: true, version: '3.12.0' }, git: { available: true, version: 'git version 2.45.0' }, xelatex: { available: true, version: 'XeLaTeX' } })
    modelingApiMock.recoveries.mockResolvedValue({ recoveries: [{ recovery_id: 'recovery-1', project_id: 'project-1', from_state: 'experiment_running', to_state: 'experiment_implementation', interrupted_run_ids: ['exp-0001'], created_at: '2026-07-12T00:00:00' }], total: 1 })
  })

  it('renders each approval only at its declared gate and removes stale approval actions', async () => {
    let state = 'model_approval_pending'
    const states = ['execution_approval_pending', 'final_approval_pending', 'commit_approval_pending', 'completed']
    modelingApiMock.advance.mockImplementation(async () => {
      state = states.shift() || 'completed'
      return { ...project, state }
    })
    modelingApiMock.listApprovals.mockImplementation(async () => ({
      approvals: state === 'model_approval_pending' ? [planApproval]
        : state === 'execution_approval_pending' ? [{ approval_id: 'execution-approval', project_id: 'project-1', gate: 'execution_approval', payload_hash: 'execution-hash', payload: {}, status: 'pending' }]
          : state === 'final_approval_pending' ? [{ approval_id: 'final-approval', project_id: 'project-1', gate: 'final_approval', payload_hash: 'final-hash', payload: {}, status: 'pending' }]
            : state === 'commit_approval_pending' ? [{ approval_id: 'commit-approval', project_id: 'project-1', gate: 'commit_approval', payload_hash: 'commit-hash', payload: {}, status: 'pending' }]
              : [],
      total: 1,
    }))
    modelingApiMock.listArtifacts.mockImplementation(async () => ({
      artifacts: state === 'final_approval_pending' ? [
        { artifact_id: 'paper-md', artifact_type: 'paper_markdown', version: 1 },
        { artifact_id: 'paper-tex', artifact_type: 'paper_latex', version: 1 },
      ] : [],
      total: state === 'final_approval_pending' ? 2 : 0,
    }))
    modelingApiMock.getArtifact.mockImplementation(async (_projectId: string, artifactId: string) => ({
      artifact_id: artifactId,
      content: artifactId === 'plan-1' ? { problem_summary: 'Forecast sales', candidates: [] }
        : artifactId === 'paper-md' ? '# Draft'
          : '\\begin{document}Draft\\end{document}',
    }))
    modelingApiMock.listExperiments.mockImplementation(async () => ({
      experiments: state === 'execution_approval_pending' ? [{
        experiment_id: 'exp-0001', execution_payload_hash: 'execution-hash', status: 'prepared',
        config: { model: { kind: 'linear_regression' }, seed: 42, metrics: [] },
        execution_batch: { experiment_id: 'exp-0001', commands: [['python', 'src/train.py']], timeout_seconds: 60, max_output_bytes: 4096, network_allowed: false, code_hash: 'code-hash', input_hashes: {}, source_hashes: {}, dependency_lock: '', dependency_diff: [] },
      }] : [],
      total: 1,
    }))
    modelingApiMock.gitStatus.mockResolvedValue({ paths: ['deliverables/paper.pdf'] })
    modelingApiMock.reviewGit.mockResolvedValue({ ok: true, paths: ['deliverables/paper.pdf'], diff: 'diff', issues: [] })
    render(<ModelingProjectsView />)

    expect(await screen.findByText('Runtime readiness')).toBeInTheDocument()
    expect(await screen.findByText('Recovered interrupted workflow')).toBeInTheDocument()
    expect(await screen.findByText('Model plan approval')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Advance project' }))
    await waitFor(() => expect(modelingApiMock.advance).toHaveBeenCalledWith('project-1'))
    await waitFor(() => expect(screen.queryByRole('button', { name: 'Approve plan' })).not.toBeInTheDocument())
    expect(await screen.findByText('Experiment execution approval')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Advance project' }))
    expect(await screen.findByLabelText('Paper workspace')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Approve execution' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Approve final paper' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Advance project' }))
    expect(await screen.findByText('Git commit approval')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Approve final paper' })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Advance project' }))
    await waitFor(() => expect(screen.queryByText('Git commit approval')).not.toBeInTheDocument())
  })
})
