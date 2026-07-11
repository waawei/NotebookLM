import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const modelingApiMock = vi.hoisted(() => ({
  list: vi.fn(), get: vi.fn(), create: vi.fn(), advance: vi.fn(), rollback: vi.fn(), uploadInput: vi.fn(),
  listArtifacts: vi.fn(), getArtifact: vi.fn(), listApprovals: vi.fn(), decideApproval: vi.fn(),
  listExperiments: vi.fn(), prepareExperiment: vi.fn(), requestExecution: vi.fn(), executeExperiment: vi.fn(),
  createPaperDraft: vi.fn(), savePaperMarkdown: vi.fn(), renderPaper: vi.fn(), reviewPaper: vi.fn(), requestFinalApproval: vi.fn(), compilePaper: vi.fn(), paperPdfUrl: vi.fn(),
  listPaperReviews: vi.fn(),
  checkDeliverables: vi.fn(), listDeliverables: vi.fn(), buildDeliverables: vi.fn(), gitStatus: vi.fn(), reviewGit: vi.fn(), requestCommit: vi.fn(), commit: vi.fn(),
  runtime: vi.fn(), recoveries: vi.fn(), dismissRecovery: vi.fn(), parseProblem: vi.fn(), profileData: vi.fn(), createModelPlan: vi.fn(),
}))
vi.mock('../services/api', () => ({ modelingApi: modelingApiMock }))

import ModelingProjectsView from './ModelingProjectsView'
import { useStore } from '../store/useStore'

const project = { project_id: 'project-1', name: 'Fixture Forecast', slug: 'fixture-forecast', workspace_path: 'C:/workspace/fixture-forecast', state: 'model_approval_pending' }
const planApproval = { approval_id: 'model-approval', project_id: 'project-1', gate: 'model_approval', payload_hash: 'plan-hash', payload: { artifact_id: 'plan-1', artifact_sha256: 'plan-sha', version: 1 }, status: 'pending' }
const executionBatch = { experiment_id: 'exp-0001', commands: [['python', 'src/train.py']], timeout_seconds: 60, max_output_bytes: 4096, network_allowed: false, code_hash: 'code-hash', input_hashes: {}, source_hashes: {}, dependency_lock: '', dependency_diff: [] }

describe('ModelingProjectsView workflow integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useStore.setState({ selectedModelingProjectId: null })
  })

  it('drives approvals, two experiments, paper review, deliverables, and Git commit through their real controls', async () => {
    let state = 'model_approval_pending'
    let experimentCount = 0
    let executionApprovalRequested = false
    let executionApproved = false
    let paperReviewed = false
    let finalRequested = false
    let commitRequested = false
    let commitApproved = false
    const currentProject = () => ({ ...project, state })
    const experiment = (index: number) => ({ experiment_id: `exp-000${index}`, execution_payload_hash: `execution-hash-${index}`, status: 'prepared', config: { model: { kind: index === 1 ? 'mean_baseline' : 'linear_regression' }, seed: 42, metrics: [] }, execution_batch: { ...executionBatch, experiment_id: `exp-000${index}` } })

    modelingApiMock.list.mockImplementation(async () => ({ projects: [currentProject()], total: 1 }))
    modelingApiMock.get.mockImplementation(async () => currentProject())
    modelingApiMock.listArtifacts.mockImplementation(async () => ({
      artifacts: (state === 'model_approval_pending' ? [{ artifact_id: 'plan-1', artifact_type: 'model_plan', version: 1 }] : [])
        .concat(['consistency_review', 'final_approval_pending', 'packaging'].includes(state) ? [{ artifact_id: 'paper-md', artifact_type: 'paper_markdown', version: 1 }, { artifact_id: 'paper-tex', artifact_type: 'paper_latex', version: 1 }] : []),
      total: 3,
    }))
    modelingApiMock.getArtifact.mockImplementation(async (_projectId: string, artifactId: string) => ({ artifact_id: artifactId, content: artifactId === 'plan-1' ? { problem_summary: 'Forecast sales', candidates: [{ name: 'mean baseline', assumptions: [], features: [], algorithm: 'mean', metrics: [], risks: [] }, { name: 'linear regression', assumptions: [], features: [], algorithm: 'linear', metrics: [], risks: [] }] } : artifactId === 'paper-md' ? '# Draft' : '\\begin{document}Draft\\end{document}' }))
    modelingApiMock.listApprovals.mockImplementation(async () => ({
      approvals: state === 'model_approval_pending' ? [planApproval]
        : state === 'execution_approval_pending' && executionApprovalRequested ? [{ approval_id: `execution-${experimentCount}`, project_id: 'project-1', gate: 'execution_approval', payload_hash: `execution-hash-${experimentCount}`, payload: {}, status: 'pending' }]
          : state === 'final_approval_pending' && finalRequested ? [{ approval_id: 'final-approval', project_id: 'project-1', gate: 'final_approval', payload_hash: 'final-hash', payload: {}, status: 'pending' }]
            : state === 'commit_approval_pending' && commitRequested ? [{ approval_id: 'commit-approval', project_id: 'project-1', gate: 'commit_approval', payload_hash: 'commit-hash', payload: { paths: ['deliverables/paper.pdf'], diff_hash: 'diff-hash', file_hashes: { 'deliverables/paper.pdf': 'paper-hash' }, manifest_hash: 'manifest-hash', commit_message: 'feat: add fixture modeling solution' }, status: commitApproved ? 'approved' : 'pending' }]
              : [], total: 1,
    }))
    modelingApiMock.listExperiments.mockImplementation(async () => ({ experiments: ['execution_approval_pending', 'experiment_running'].includes(state) ? [{ ...experiment(experimentCount), status: executionApproved ? 'prepared' : 'prepared' }] : [], total: experimentCount }))
    modelingApiMock.runtime.mockResolvedValue({ workspace: { configured: true, writable: true }, python: { available: true, version: '3.12.0' }, git: { available: true, version: 'git version' }, xelatex: { available: true, version: 'XeLaTeX' } })
    modelingApiMock.recoveries.mockResolvedValue({ recoveries: [{ recovery_id: 'recovery-1', project_id: 'project-1', from_state: 'experiment_running', to_state: 'experiment_implementation', interrupted_run_ids: ['exp-0001'], created_at: '2026-07-12T00:00:00' }], total: 1 })
    modelingApiMock.decideApproval.mockImplementation(async (_projectId: string, approvalId: string) => { if (approvalId === 'model-approval') state = 'experiment_implementation'; else if (approvalId.startsWith('execution-')) { executionApproved = true; executionApprovalRequested = false; state = 'experiment_running' } else if (approvalId === 'final-approval') state = 'packaging'; else if (approvalId === 'commit-approval') commitApproved = true; return {} })
    modelingApiMock.prepareExperiment.mockImplementation(async () => { experimentCount += 1; executionApprovalRequested = false; executionApproved = false; state = 'execution_approval_pending'; return experiment(experimentCount) })
    modelingApiMock.requestExecution.mockImplementation(async () => { executionApprovalRequested = true; return {} })
    modelingApiMock.executeExperiment.mockImplementation(async () => { state = experimentCount < 2 ? 'experiment_implementation' : 'result_validation'; return {} })
    modelingApiMock.advance.mockImplementation(async () => { if (state === 'result_validation') state = 'paper_drafting'; else if (state === 'paper_drafting') state = 'consistency_review'; else if (state === 'packaging') state = 'commit_approval_pending'; return currentProject() })
    modelingApiMock.createPaperDraft.mockImplementation(async () => { state = 'consistency_review'; return {} })
    modelingApiMock.renderPaper.mockResolvedValue({ rendered: '# Draft', claims: [] })
    modelingApiMock.reviewPaper.mockImplementation(async () => { paperReviewed = true; return { status: 'passed', issues: [] } })
    modelingApiMock.listPaperReviews.mockImplementation(async () => ({ reviews: paperReviewed ? [{ status: 'passed', issues: [] }] : [], total: paperReviewed ? 1 : 0 }))
    modelingApiMock.requestFinalApproval.mockImplementation(async () => { if (paperReviewed) { finalRequested = true; state = 'final_approval_pending' }; return {} })
    modelingApiMock.compilePaper.mockResolvedValue({})
    modelingApiMock.checkDeliverables.mockResolvedValue({ ok: true, issues: [] })
    modelingApiMock.listDeliverables.mockResolvedValue({ artifacts: [], total: 0 })
    modelingApiMock.buildDeliverables.mockResolvedValue({})
    modelingApiMock.gitStatus.mockResolvedValue({ paths: ['deliverables/paper.pdf'] })
    modelingApiMock.reviewGit.mockResolvedValue({ ok: true, paths: ['deliverables/paper.pdf'], diff: 'diff', diff_hash: 'diff-hash', file_hashes: { 'deliverables/paper.pdf': 'paper-hash' }, manifest_hash: 'manifest-hash', issues: [] })
    modelingApiMock.requestCommit.mockImplementation(async () => { commitRequested = true; return {} })
    modelingApiMock.commit.mockImplementation(async () => { state = 'completed'; return {} })
    modelingApiMock.paperPdfUrl.mockReturnValue('/paper.pdf')

    render(<ModelingProjectsView />)
    expect(await screen.findByText('Runtime readiness')).toBeInTheDocument()
    expect(await screen.findByText('Recovered interrupted workflow')).toBeInTheDocument()
    modelingApiMock.dismissRecovery.mockResolvedValue({})
    fireEvent.click(screen.getByRole('button', { name: 'Dismiss recovery notice' }))
    await waitFor(() => expect(modelingApiMock.dismissRecovery).toHaveBeenCalledWith('recovery-1'))
    fireEvent.click(await screen.findByRole('button', { name: 'Approve plan' }))
    await waitFor(() => expect(modelingApiMock.decideApproval).toHaveBeenCalledWith('project-1', 'model-approval', expect.objectContaining({ payload_hash: 'plan-hash' })))
    expect(await screen.findByRole('button', { name: 'Prepare experiment' })).toBeInTheDocument()

    for (const index of [1, 2]) {
      fireEvent.click(screen.getByRole('button', { name: 'Prepare experiment' }))
      expect(await screen.findByRole('button', { name: `Request execution approval: exp-000${index}` })).toBeInTheDocument()
      fireEvent.click(screen.getByRole('button', { name: `Request execution approval: exp-000${index}` }))
      expect(await screen.findByText('Experiment execution approval')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Approve execution' })).toBeInTheDocument()
      fireEvent.click(screen.getByRole('button', { name: 'Approve execution' }))
      await waitFor(() => expect(screen.queryByRole('button', { name: 'Approve execution' })).not.toBeInTheDocument())
      fireEvent.click(await screen.findByRole('button', { name: 'Run' }))
      if (index === 1) expect(await screen.findByRole('button', { name: 'Prepare experiment' })).toBeInTheDocument()
    }

    fireEvent.click(screen.getByRole('button', { name: 'Advance project' }))
    expect(await screen.findByRole('button', { name: 'Generate paper draft' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Generate paper draft' }))
    expect(await screen.findByRole('button', { name: 'Review' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Review' }))
    await waitFor(() => {
      const requestFinalApproval = screen.getByRole('button', { name: 'Request final approval' })
      expect(requestFinalApproval).toBeEnabled()
      fireEvent.click(requestFinalApproval)
      expect(modelingApiMock.requestFinalApproval).toHaveBeenCalledWith('project-1')
    })
    expect(await screen.findByRole('button', { name: 'Approve final paper' })).toBeInTheDocument()
    await waitFor(() => {
      fireEvent.click(screen.getByRole('button', { name: 'Approve final paper' }))
      expect(modelingApiMock.decideApproval).toHaveBeenCalledWith('project-1', 'final-approval', expect.objectContaining({ payload_hash: 'final-hash' }))
    })
    expect(await screen.findByRole('button', { name: 'Compile' })).toBeEnabled()
    fireEvent.click(screen.getByRole('button', { name: 'Compile' }))
    await waitFor(() => expect(modelingApiMock.compilePaper).toHaveBeenCalledWith('project-1'))
    expect(await screen.findByRole('button', { name: 'Build deliverables' })).toBeEnabled()
    fireEvent.click(screen.getByRole('button', { name: 'Build deliverables' }))
    await waitFor(() => expect(modelingApiMock.buildDeliverables).toHaveBeenCalledWith('project-1'))
    fireEvent.click(await screen.findByRole('button', { name: 'Advance project' }))
    expect(await screen.findByText('Git commit approval')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Commit message'), { target: { value: 'feat: add fixture modeling solution' } })
    fireEvent.click(screen.getByRole('button', { name: 'Request commit approval' }))
    expect(await screen.findByRole('button', { name: 'Approve commit' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Approve commit' }))
    expect(await screen.findByRole('button', { name: 'Commit approved files' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Commit approved files' }))
    await waitFor(() => expect(screen.getByText('Current state:').parentElement).toHaveTextContent('completed'))
  })

  it('removes the commit action when an approved Git diff becomes stale', async () => {
    const commitProject = { ...project, state: 'commit_approval_pending' }
    modelingApiMock.list.mockResolvedValue({ projects: [commitProject], total: 1 })
    modelingApiMock.get.mockResolvedValue(commitProject)
    modelingApiMock.listArtifacts.mockResolvedValue({ artifacts: [], total: 0 })
    modelingApiMock.listApprovals.mockResolvedValue({ approvals: [{ approval_id: 'commit-approval', project_id: 'project-1', gate: 'commit_approval', payload_hash: 'commit-hash', payload: { paths: ['deliverables/paper.pdf'], diff_hash: 'approved-diff', file_hashes: { 'deliverables/paper.pdf': 'paper-hash' }, manifest_hash: 'manifest-hash', commit_message: 'feat: add fixture modeling solution' }, status: 'approved' }], total: 1 })
    modelingApiMock.listExperiments.mockResolvedValue({ experiments: [], total: 0 })
    modelingApiMock.runtime.mockResolvedValue({ workspace: { configured: true, writable: true }, python: { available: true, version: '3.12.0' }, git: { available: true, version: 'git version' }, xelatex: { available: true, version: 'XeLaTeX' } })
    modelingApiMock.recoveries.mockResolvedValue({ recoveries: [], total: 0 })
    modelingApiMock.gitStatus.mockResolvedValue({ paths: ['deliverables/paper.pdf'] })
    modelingApiMock.reviewGit.mockResolvedValue({ ok: true, paths: ['deliverables/paper.pdf'], diff: 'changed diff', diff_hash: 'changed-diff', file_hashes: { 'deliverables/paper.pdf': 'paper-hash' }, manifest_hash: 'manifest-hash', issues: [] })

    render(<ModelingProjectsView />)

    expect(await screen.findByText('Approval does not match the current review payload.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Commit approved files' })).not.toBeInTheDocument()
  })

  it('disables state-bound write actions when the workspace is unavailable', async () => {
    modelingApiMock.list.mockResolvedValue({ projects: [project], total: 1 })
    modelingApiMock.get.mockResolvedValue(project)
    modelingApiMock.listArtifacts.mockResolvedValue({ artifacts: [{ artifact_id: 'plan-1', artifact_type: 'model_plan', version: 1 }], total: 1 })
    modelingApiMock.getArtifact.mockResolvedValue({ artifact_id: 'plan-1', content: { problem_summary: 'Forecast sales', candidates: [] } })
    modelingApiMock.listApprovals.mockResolvedValue({ approvals: [planApproval], total: 1 })
    modelingApiMock.listExperiments.mockResolvedValue({ experiments: [], total: 0 })
    modelingApiMock.runtime.mockResolvedValue({ workspace: { configured: true, writable: false }, python: { available: true, version: '3.12.0' }, git: { available: true, version: 'git version' }, xelatex: { available: true, version: 'XeLaTeX' } })
    modelingApiMock.recoveries.mockResolvedValue({ recoveries: [], total: 0 })

    render(<ModelingProjectsView />)

    expect(await screen.findByText('Model plan approval')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Approve plan' })).toBeDisabled())
    expect(screen.getByRole('button', { name: 'Request changes' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Advance project' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Rollback project' })).toBeDisabled()
  })

  it('disables experiment execution when the workspace is not configured', async () => {
    const executionProject = { ...project, state: 'execution_approval_pending' }
    modelingApiMock.list.mockResolvedValue({ projects: [executionProject], total: 1 })
    modelingApiMock.get.mockResolvedValue(executionProject)
    modelingApiMock.listArtifacts.mockResolvedValue({ artifacts: [], total: 0 })
    modelingApiMock.listApprovals.mockResolvedValue({ approvals: [], total: 0 })
    modelingApiMock.listExperiments.mockResolvedValue({ experiments: [{ experiment_id: 'exp-0001', status: 'prepared', config: { model: { kind: 'linear_regression' }, seed: 42, metrics: [] }, execution_batch: executionBatch }], total: 1 })
    modelingApiMock.runtime.mockResolvedValue({ workspace: { configured: false, writable: true }, python: { available: true, version: '3.12.0' }, git: { available: true, version: 'git version' }, xelatex: { available: true, version: 'XeLaTeX' } })
    modelingApiMock.recoveries.mockResolvedValue({ recoveries: [], total: 0 })

    render(<ModelingProjectsView />)

    expect(await screen.findByRole('button', { name: 'Run' })).toBeDisabled()
  })
})
