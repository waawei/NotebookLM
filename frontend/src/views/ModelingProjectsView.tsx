import { type FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import { AlertCircle, ChevronLeft, ChevronRight, Loader2, RefreshCw } from 'lucide-react'
import { modelingApi, type ApprovalRequest, type ExecutionBatch, type ExperimentRun, type GitReview, type ModelingArtifact, type ModelingProject, type ModelPlan, type ModelingRecovery, type ModelingRuntimeStatus } from '../services/api'
import { useStore } from '../store/useStore'
import ModelingInputPanel from '../components/ModelingInputPanel'
import ModelPlanApprovalCard from '../components/ModelPlanApprovalCard'
import ExperimentApprovalCard from '../components/ExperimentApprovalCard'
import ExperimentRunPanel from '../components/ExperimentRunPanel'
import PaperWorkspace from '../components/PaperWorkspace'
import DeliveryChecklist from '../components/DeliveryChecklist'
import GitCommitApprovalCard from '../components/GitCommitApprovalCard'
import ModelingRuntimeStatusPanel from '../components/ModelingRuntimeStatus'
import ModelingRecoveryBanner from '../components/ModelingRecoveryBanner'

const MODELING_WORKFLOW_STATES = new Set([
  'project_initialized',
  'problem_parsing',
  'data_profiling',
  'model_planning',
  'model_approval_pending',
  'experiment_implementation',
  'execution_approval_pending',
  'experiment_running',
  'result_validation',
  'paper_drafting',
  'consistency_review',
  'final_approval_pending',
  'packaging',
  'commit_approval_pending',
  'committing',
  'completed',
])

const MODELING_ROLLBACK_STATES = new Set([
  'problem_parsing',
  'data_profiling',
  'model_planning',
  'model_approval_pending',
  'experiment_implementation',
  'execution_approval_pending',
  'experiment_running',
  'result_validation',
  'paper_drafting',
  'consistency_review',
  'final_approval_pending',
  'packaging',
  'commit_approval_pending',
  'committing',
])

function replaceProject(projects: ModelingProject[], project: ModelingProject) {
  return projects.map((item) => item.project_id === project.project_id ? project : item)
}

export default function ModelingProjectsView() {
  const selectedModelingProjectId = useStore((state) => state.selectedModelingProjectId)
  const setSelectedModelingProjectId = useStore((state) => state.setSelectedModelingProjectId)
  const [projects, setProjects] = useState<ModelingProject[]>([])
  const [name, setName] = useState('')
  const [rollbackReason, setRollbackReason] = useState('')
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [transitioning, setTransitioning] = useState(false)
  const [stageBusy, setStageBusy] = useState(false)
  const [artifacts, setArtifacts] = useState<ModelingArtifact[]>([])
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([])
  const [modelPlan, setModelPlan] = useState<ModelPlan | null>(null)
  const [experiments, setExperiments] = useState<ExperimentRun[]>([])
  const [gitReview, setGitReview] = useState<GitReview | null>(null)
  const [runtimeStatus, setRuntimeStatus] = useState<ModelingRuntimeStatus | null>(null)
  const [recoveries, setRecoveries] = useState<ModelingRecovery[]>([])
  const [evidenceProjectId, setEvidenceProjectId] = useState<string | null>(null)
  const [error, setError] = useState('')
  const evidenceGeneration = useRef(0)

  const selectedProject = useMemo(
    () => projects.find((project) => project.project_id === selectedModelingProjectId) || projects[0] || null,
    [projects, selectedModelingProjectId],
  )
  const canAdvance = Boolean(
    selectedProject
    && MODELING_WORKFLOW_STATES.has(selectedProject.state)
    && selectedProject.state !== 'completed',
  )
  const canRollback = Boolean(selectedProject && MODELING_ROLLBACK_STATES.has(selectedProject.state))
  const workspaceReady = Boolean(runtimeStatus?.workspace.configured && runtimeStatus?.workspace.writable)

  const loadProjects = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await modelingApi.list()
      setProjects(data.projects)
      setSelectedModelingProjectId(
        selectedModelingProjectId && data.projects.some((project) => project.project_id === selectedModelingProjectId)
          ? selectedModelingProjectId
          : data.projects[0]?.project_id || null,
      )
    } catch {
      setError('Unable to load modeling projects. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadProjects()
  }, [])

  useEffect(() => {
    let active = true
    void Promise.all([modelingApi.runtime(), modelingApi.recoveries()]).then(([runtime, recoveryData]) => {
      if (!active) return
      setRuntimeStatus(runtime)
      setRecoveries(recoveryData.recoveries)
    }).catch(() => {
      if (active) setError('Unable to load modeling runtime readiness. Please try again.')
    })
    return () => { active = false }
  }, [])

  const loadEvidence = async (projectId: string) => {
    const generation = ++evidenceGeneration.current
    setArtifacts([])
    setApprovals([])
    setModelPlan(null)
    setEvidenceProjectId(null)
    try {
      const [artifactData, approvalData] = await Promise.all([
        modelingApi.listArtifacts(projectId),
        modelingApi.listApprovals(projectId),
      ])
      const experimentData = typeof modelingApi.listExperiments === 'function'
        ? await modelingApi.listExperiments(projectId)
        : { experiments: [], total: 0 }
      if (generation !== evidenceGeneration.current) return
      const paperArtifacts = artifactData.artifacts.filter((item) => item.artifact_type === 'paper_markdown' || item.artifact_type === 'paper_latex')
      const paperContents = await Promise.all(paperArtifacts.map((item) => modelingApi.getArtifact(projectId, item.artifact_id)))
      if (generation !== evidenceGeneration.current) return
      const contentById = new Map(paperContents.map((item) => [item.artifact_id, item.content]))
      setArtifacts(artifactData.artifacts.map((item) => contentById.has(item.artifact_id) ? { ...item, content: contentById.get(item.artifact_id) } : item))
      setApprovals(approvalData.approvals)
      setExperiments(experimentData.experiments)
      if (selectedProject?.state === 'commit_approval_pending' && runtimeStatus?.git.available && typeof modelingApi.reviewGit === 'function') {
        const status = await modelingApi.gitStatus(projectId)
        const candidates = status.paths
        if (candidates.length) setGitReview(await modelingApi.reviewGit(projectId, candidates))
      } else setGitReview(null)
      const pending = approvalData.approvals
        .filter((item) => item.gate === 'model_approval' && item.status === 'pending')
        .sort((left, right) => {
          const created = (right.created_at || '').localeCompare(left.created_at || '')
          if (created !== 0) return created
          const version = (right.payload?.version || 0) - (left.payload?.version || 0)
          return version || right.approval_id.localeCompare(left.approval_id)
        })[0]
      if (pending) {
        if (!pending.payload.artifact_id) throw new Error('Model approval payload is incomplete')
        const planArtifact = await modelingApi.getArtifact(projectId, pending.payload.artifact_id)
        if (generation !== evidenceGeneration.current) return
        setModelPlan(planArtifact.content as ModelPlan)
        setEvidenceProjectId(projectId)
      } else {
        setModelPlan(null)
        setEvidenceProjectId(projectId)
      }
    } catch {
      if (generation === evidenceGeneration.current) {
        setError('Unable to load modeling evidence. Please try again.')
      }
    }
  }

  const refreshProject = async (projectId: string) => {
    const project = await modelingApi.get(projectId)
    setProjects((current) => replaceProject(current, project))
    setSelectedModelingProjectId(project.project_id)
    await loadEvidence(projectId)
  }

  useEffect(() => {
    if (selectedProject) void loadEvidence(selectedProject.project_id)
    else {
      setArtifacts([])
      setApprovals([])
      setModelPlan(null)
      setExperiments([])
      setEvidenceProjectId(null)
    }
  }, [selectedProject?.project_id, selectedProject?.state, runtimeStatus?.git.available])

  const createProject = async (event: FormEvent) => {
    event.preventDefault()
    const cleanName = name.trim()
    if (!cleanName) return
    setSubmitting(true)
    setError('')
    try {
      const project = await modelingApi.create({ name: cleanName })
      setProjects((current) => [project, ...current])
      setSelectedModelingProjectId(project.project_id)
      setName('')
    } catch {
      setError('Unable to create the modeling project. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const transitionProject = async (direction: 'advance' | 'rollback') => {
    if (!selectedProject) return
    setTransitioning(true)
    setError('')
    try {
      const project = direction === 'advance'
        ? await modelingApi.advance(selectedProject.project_id)
        : await modelingApi.rollback(selectedProject.project_id, rollbackReason.trim())
      setProjects((current) => replaceProject(current, project))
      setSelectedModelingProjectId(project.project_id)
      if (direction === 'rollback') setRollbackReason('')
    } catch {
      setError(`Unable to ${direction} the modeling project. Please try again.`)
    } finally {
      setTransitioning(false)
    }
  }

  const runStageAction = async () => {
    if (!selectedProject) return
    setStageBusy(true)
    setError('')
    try {
      if (selectedProject.state === 'problem_parsing') {
        await modelingApi.parseProblem(selectedProject.project_id)
      } else if (selectedProject.state === 'data_profiling') {
        const dataInput = [...artifacts].reverse().find((item) => item.artifact_type === 'data_input')
        if (!dataInput) throw new Error('Data input missing')
        await modelingApi.profileData(selectedProject.project_id, dataInput.artifact_id)
      } else if (selectedProject.state === 'model_planning') {
        await modelingApi.createModelPlan(selectedProject.project_id)
      }
      await loadEvidence(selectedProject.project_id)
    } catch {
      setError('Unable to run the current modeling stage. Please check its inputs.')
    } finally {
      setStageBusy(false)
    }
  }

  const pendingModelApproval = evidenceProjectId === selectedProject?.project_id ? approvals
    .filter((item) => item.gate === 'model_approval' && item.status === 'pending')
    .sort((left, right) => {
      const created = (right.created_at || '').localeCompare(left.created_at || '')
      if (created !== 0) return created
      return (right.payload?.version || 0) - (left.payload?.version || 0)
    })[0] : undefined
  const pendingExecutionApproval = evidenceProjectId === selectedProject?.project_id ? approvals
    .filter((item) => item.gate === 'execution_approval' && item.status === 'pending')[0] : undefined
  const approvalExperiment = pendingExecutionApproval ? experiments.find((item) => item.execution_payload_hash === pendingExecutionApproval.payload_hash) : undefined
  const paperMarkdown = artifacts.filter((item) => item.artifact_type === 'paper_markdown').sort((left, right) => right.version - left.version)[0]
  const paperLatex = artifacts.filter((item) => item.artifact_type === 'paper_latex').sort((left, right) => right.version - left.version)[0]
  const pendingFinalApproval = evidenceProjectId === selectedProject?.project_id ? approvals.filter((item) => item.gate === 'final_approval' && item.status === 'pending')[0] : undefined
  const latestCommitApproval = evidenceProjectId === selectedProject?.project_id ? approvals.filter((item) => item.gate === 'commit_approval').sort((left, right) => (right.created_at || '').localeCompare(left.created_at || ''))[0] : undefined

  const prepareExperiment = async () => {
    if (!selectedProject) return
    setStageBusy(true)
    setError('')
    try {
      await modelingApi.prepareExperiment(selectedProject.project_id, experiments.length)
      await refreshProject(selectedProject.project_id)
    } catch { setError('Unable to prepare the approved experiment.') } finally { setStageBusy(false) }
  }

  const requestExecution = async (experimentId: string) => {
    if (!selectedProject) return
    setStageBusy(true)
    setError('')
    try {
      await modelingApi.requestExecution(selectedProject.project_id, experimentId)
      await refreshProject(selectedProject.project_id)
    } catch { setError('Unable to request experiment execution approval.') } finally { setStageBusy(false) }
  }

  const executeExperiment = async (experimentId: string) => {
    if (!selectedProject) return
    setStageBusy(true)
    setError('')
    try {
      await modelingApi.executeExperiment(selectedProject.project_id, experimentId)
      await refreshProject(selectedProject.project_id)
    } catch { setError('Unable to execute the approved experiment.') } finally { setStageBusy(false) }
  }

  return (
    <div className="grid h-full grid-cols-[minmax(260px,340px)_1fr] bg-gray-100 dark:bg-gray-950">
      <aside className="min-h-0 border-r border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
        <div className="border-b border-gray-200 p-4 dark:border-gray-800">
          <div className="mb-3 flex items-center justify-between gap-2">
            <div>
              <h2 className="text-sm font-semibold text-gray-950 dark:text-gray-100">Modeling projects</h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">{projects.length} saved projects</p>
            </div>
            <button onClick={() => void loadProjects()} disabled={loading} className="flex h-9 w-9 items-center justify-center rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:cursor-not-allowed dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800" aria-label="Refresh projects" title="Refresh projects">
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
          <form onSubmit={createProject} className="flex gap-2">
            <label className="sr-only" htmlFor="project-name">Project name</label>
            <input id="project-name" aria-label="Project name" value={name} onChange={(event) => setName(event.target.value)} placeholder="Project name" className="min-w-0 flex-1 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800 outline-none focus:border-blue-500 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100" />
            <button disabled={!name.trim() || submitting || runtimeStatus !== null && !workspaceReady} className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300 dark:disabled:bg-gray-700">
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create project'}
            </button>
          </form>
        </div>
        <div className="min-h-0 overflow-y-auto p-3">
          {loading && projects.length === 0 ? (
            <div className="flex justify-center gap-2 py-12 text-sm text-gray-500"><Loader2 className="h-4 w-4 animate-spin" />Loading projects</div>
          ) : projects.length === 0 ? (
            <p className="py-12 text-center text-sm text-gray-500">No modeling projects yet.</p>
          ) : (
            <div className="space-y-2">
              {projects.map((project) => <button key={project.project_id} onClick={() => setSelectedModelingProjectId(project.project_id)} className={`w-full rounded-lg border p-3 text-left transition-colors ${selectedProject?.project_id === project.project_id ? 'border-blue-400 bg-blue-50 dark:border-blue-800 dark:bg-blue-950' : 'border-gray-200 bg-white hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-900 dark:hover:bg-gray-800'}`}><p className="truncate text-sm font-medium text-gray-950 dark:text-gray-100">{project.name}</p><p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{project.state}</p></button>)}
            </div>
          )}
        </div>
      </aside>
      <main className="min-w-0 overflow-y-auto p-6">
        {error && <div role="alert" className="mx-auto mb-4 flex max-w-4xl items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200"><AlertCircle className="h-4 w-4 shrink-0" />{error}</div>}
        {runtimeStatus && <div className="mx-auto mb-4 max-w-4xl"><ModelingRuntimeStatusPanel status={runtimeStatus} /></div>}
        {selectedProject ? (
          <article className="mx-auto max-w-4xl rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
            <div className="border-b border-gray-100 pb-4 dark:border-gray-800"><h1 className="text-xl font-semibold text-gray-950 dark:text-gray-100">{selectedProject.name}</h1><p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Current state: <span className="font-medium">{selectedProject.state}</span></p>{selectedProject.deadline && <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Deadline: {selectedProject.deadline}</p>}</div>
            <dl className="mt-5 grid gap-4 text-sm sm:grid-cols-2"><div><dt className="text-xs font-medium text-gray-500">Project slug</dt><dd className="mt-1 text-gray-900 dark:text-gray-100">{selectedProject.slug}</dd></div><div><dt className="text-xs font-medium text-gray-500">Workspace</dt><dd className="mt-1 break-all text-gray-900 dark:text-gray-100">{selectedProject.workspace_path}</dd></div></dl>
            <div className="mt-5 space-y-4">
              {recoveries.filter((recovery) => recovery.project_id === selectedProject.project_id).map((recovery) => <ModelingRecoveryBanner key={recovery.recovery_id} recovery={recovery} onDismissed={(recoveryId) => setRecoveries((current) => current.filter((item) => item.recovery_id !== recoveryId))} />)}
              {selectedProject.state === 'project_initialized' && <ModelingInputPanel projectId={selectedProject.project_id} disabled={!workspaceReady} onChanged={() => loadEvidence(selectedProject.project_id)} />}
              {selectedProject.state === 'problem_parsing' && <button type="button" disabled={stageBusy || !workspaceReady} onClick={() => void runStageAction()} className="rounded bg-indigo-600 px-3 py-2 text-sm font-medium text-white disabled:bg-gray-400">Parse problem</button>}
              {selectedProject.state === 'data_profiling' && <button type="button" disabled={stageBusy || !workspaceReady || !artifacts.some((item) => item.artifact_type === 'data_input')} onClick={() => void runStageAction()} className="rounded bg-indigo-600 px-3 py-2 text-sm font-medium text-white disabled:bg-gray-400">Profile data</button>}
              {selectedProject.state === 'model_planning' && <button type="button" disabled={stageBusy || !workspaceReady} onClick={() => void runStageAction()} className="rounded bg-indigo-600 px-3 py-2 text-sm font-medium text-white disabled:bg-gray-400">Create model plan</button>}
              {selectedProject.state === 'model_approval_pending' && pendingModelApproval && modelPlan && <ModelPlanApprovalCard key={pendingModelApproval.approval_id} projectId={selectedProject.project_id} approval={pendingModelApproval} plan={modelPlan} onDecided={() => refreshProject(selectedProject.project_id)} />}
              {selectedProject.state === 'experiment_implementation' && <button type="button" disabled={stageBusy || !workspaceReady || !runtimeStatus?.python.available} onClick={() => void prepareExperiment()} className="rounded bg-indigo-600 px-3 py-2 text-sm font-medium text-white disabled:bg-gray-400">Prepare experiment</button>}
              {selectedProject.state === 'execution_approval_pending' && experiments.filter((item) => item.status === 'prepared').map((item) => <button key={item.experiment_id} type="button" disabled={stageBusy} onClick={() => void requestExecution(item.experiment_id)} className="mr-2 rounded bg-indigo-600 px-3 py-2 text-sm font-medium text-white disabled:bg-gray-400">Request execution approval: {item.experiment_id}</button>)}
              {selectedProject.state === 'execution_approval_pending' && pendingExecutionApproval && approvalExperiment?.execution_batch && <ExperimentApprovalCard projectId={selectedProject.project_id} approval={pendingExecutionApproval} batch={approvalExperiment.execution_batch as ExecutionBatch} onDecided={() => refreshProject(selectedProject.project_id)} />}
              {experiments.length > 0 && <ExperimentRunPanel projectId={selectedProject.project_id} experiments={experiments} canExecute={Boolean(runtimeStatus?.workspace.writable && runtimeStatus?.python.available)} onChanged={() => void refreshProject(selectedProject.project_id)} onExecute={(experimentId) => void executeExperiment(experimentId)} />}
              {['paper_drafting', 'consistency_review', 'final_approval_pending'].includes(selectedProject.state) && (!paperMarkdown || !paperLatex) && <button type="button" disabled={stageBusy || !workspaceReady} onClick={async () => { setStageBusy(true); try { await modelingApi.createPaperDraft(selectedProject.project_id); await refreshProject(selectedProject.project_id) } catch { setError('Unable to generate the paper draft.') } finally { setStageBusy(false) } }} className="rounded bg-indigo-600 px-3 py-2 text-sm font-medium text-white disabled:bg-gray-400">Generate paper draft</button>}
              {paperMarkdown && paperLatex && <PaperWorkspace projectId={selectedProject.project_id} markdown={String(paperMarkdown.content || '')} latex={String(paperLatex.content || '')} approval={selectedProject.state === 'final_approval_pending' ? pendingFinalApproval : undefined} canWrite={workspaceReady} canCompile={workspaceReady && (runtimeStatus?.xelatex.available ?? false)} onChanged={() => refreshProject(selectedProject.project_id)} />}
              {selectedProject.state === 'packaging' && <DeliveryChecklist projectId={selectedProject.project_id} canBuild={workspaceReady} onChanged={() => refreshProject(selectedProject.project_id)} />}
              {selectedProject.state === 'commit_approval_pending' && gitReview && <GitCommitApprovalCard projectId={selectedProject.project_id} review={gitReview} approval={latestCommitApproval} canCommit={runtimeStatus?.git.available ?? false} onChanged={() => refreshProject(selectedProject.project_id)} />}
              {artifacts.length > 0 && <section aria-label="Modeling artifacts" className="rounded border border-gray-200 p-3 dark:border-gray-800"><h2 className="text-sm font-semibold">Artifacts</h2><ul className="mt-2 space-y-1 text-xs text-gray-600 dark:text-gray-300">{artifacts.map((artifact) => <li key={artifact.artifact_id}>{artifact.artifact_type}: {artifact.relative_path}</li>)}</ul></section>}
            </div>
            <div className="mt-6 flex flex-wrap items-end gap-3 border-t border-gray-100 pt-5 dark:border-gray-800">
              <button onClick={() => void transitionProject('advance')} disabled={transitioning || !canAdvance} className="inline-flex items-center gap-1 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300 dark:disabled:bg-gray-700"><ChevronRight className="h-4 w-4" />Advance project</button>
              <label className="min-w-[200px] flex-1"><span className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-300">Rollback reason</span><input aria-label="Rollback reason" value={rollbackReason} onChange={(event) => setRollbackReason(event.target.value)} className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800 outline-none focus:border-blue-500 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100" /></label>
              <button onClick={() => void transitionProject('rollback')} disabled={transitioning || !canRollback} className="inline-flex items-center gap-1 rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"><ChevronLeft className="h-4 w-4" />Rollback project</button>
            </div>
          </article>
        ) : <div className="flex h-full items-center justify-center text-sm text-gray-500">Create or select a modeling project</div>}
      </main>
    </div>
  )
}
