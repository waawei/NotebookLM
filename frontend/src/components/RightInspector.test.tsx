import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const noteApiMock = vi.hoisted(() => ({
  list: vi.fn(),
}))
const settingsApiMock = vi.hoisted(() => ({
  getStatus: vi.fn(),
}))
const skillsApiMock = vi.hoisted(() => ({
  list: vi.fn(),
}))
const outputApiMock = vi.hoisted(() => ({
  list: vi.fn(),
}))
const previewApiMock = vi.hoisted(() => ({
  get: vi.fn(),
}))
const agentsApiMock = vi.hoisted(() => ({
  listRuns: vi.fn(),
}))

vi.mock('../services/api', () => ({
  noteApi: noteApiMock,
  settingsApi: settingsApiMock,
  skillsApi: skillsApiMock,
  outputApi: outputApiMock,
  previewApi: previewApiMock,
  agentsApi: agentsApiMock,
}))

function resolveWorkspaceApis() {
  noteApiMock.list.mockResolvedValue({ notes: [] })
  settingsApiMock.getStatus.mockResolvedValue(null)
  skillsApiMock.list.mockResolvedValue({
      skills: [
        {
          skill_id: 'paper_planner',
          name: 'Paper Planner',
          description: 'Build a paper outline.',
          allowed_tools: ['retrieval.search'],
          prompt_template: '',
          output_kind: 'outline',
        },
      ],
  })
  outputApiMock.list.mockResolvedValue({
    outputs: [
      {
        output_id: 'out-1',
        kind: 'outline',
        title: 'Chapter 2 Outline',
        content: '',
        source_doc_ids: ['doc-1'],
        created_at: '2026-07-10T10:00:00',
        updated_at: '2026-07-10T10:00:00',
      },
    ],
    total: 1,
  })
  agentsApiMock.listRuns.mockResolvedValue({
    runs: [
      {
        run_id: 'run-1',
        skill_id: 'paper_planner',
        status: 'completed',
        input_payload: { request: 'Build an outline' },
        output_id: 'out-1',
        error: null,
        steps: [],
      },
    ],
    total: 1,
  })
  previewApiMock.get.mockResolvedValue({
    type: 'output',
    id: 'out-1',
    title: 'Chapter 2 Outline',
    content_preview: 'Outline content',
    metadata: {},
    links: [],
  })
}

import { useStore } from '../store/useStore'
import RightInspector from './RightInspector'

describe('RightInspector workspace panel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    noteApiMock.list.mockImplementation(() => new Promise(() => {}))
    settingsApiMock.getStatus.mockImplementation(() => new Promise(() => {}))
    skillsApiMock.list.mockImplementation(() => new Promise(() => {}))
    outputApiMock.list.mockImplementation(() => new Promise(() => {}))
    previewApiMock.get.mockImplementation(() => new Promise(() => {}))
    agentsApiMock.listRuns.mockImplementation(() => new Promise(() => {}))
    useStore.setState({
      messages: [],
      selectedDocIds: [],
      conversationId: null,
      isLoading: false,
      suggestedQuestions: [],
      previewTarget: null,
      artifactRefreshToken: 0,
      pendingSkillCommand: null,
    })
  })

  it('uses a quiet Workspace shell with pale active tabs and citation cards', () => {
    useStore.setState({
      messages: [
        {
          role: 'assistant',
          content: 'The answer cites the source.',
          citations: [
            {
              number: 1,
              doc_id: 'doc-1',
              doc_name: 'Research Brief.pdf',
              page: 4,
              chunk_id: 2,
              content: 'A supporting passage from the document.',
              relevance_score: 0.92,
            },
          ],
        },
      ],
    })

    render(<RightInspector />)

    expect(screen.getByTestId('right-workspace-panel')).toHaveClass('bg-[#f8f7f6]')
    expect(screen.getByRole('heading', { name: 'Workspace' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Preview' })).toBeInTheDocument()

    const activeTab = screen.getByRole('button', { name: 'Workspace' })
    expect(activeTab).toHaveClass('bg-blue-50')
    expect(activeTab).toHaveClass('text-blue-700')
    expect(activeTab).not.toHaveClass('bg-blue-600')

    const citationCard = screen.getByTestId('workspace-citation-card')
    expect(citationCard).toHaveClass('bg-white')
    expect(citationCard).toHaveClass('border-[#e2e1de]')
    expect(citationCard).not.toHaveClass('bg-blue-50')

    expect(screen.getByText('#1')).toHaveClass('bg-blue-50')
    expect(screen.getByText('#1')).not.toHaveClass('bg-blue-600')
  })

  it('renders workspace tool, skill, artifact, and evidence sections in neutral cards', async () => {
    resolveWorkspaceApis()
    useStore.setState({
      messages: [
        {
          role: 'assistant',
          content: 'The answer cites the source.',
          citations: [
            {
              number: 1,
              doc_id: 'doc-1',
              doc_name: 'Research Brief.pdf',
              page: 4,
              chunk_id: 2,
              content: 'A supporting passage from the document.',
              relevance_score: 0.92,
            },
          ],
        },
      ],
    })

    render(<RightInspector />)

    expect(screen.getByRole('heading', { name: 'Tools' })).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'Skills' })).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'Tasks' })).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'Artifacts' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Evidence' })).toBeInTheDocument()

    const skillCard = await screen.findByTestId('workspace-skill-card-paper_planner')
    expect(skillCard).toHaveClass('bg-white')
    expect(skillCard).toHaveClass('border-[#e2e1de]')
  })

  it('opens Preview when an artifact card is selected', async () => {
    resolveWorkspaceApis()
    render(<RightInspector />)

    fireEvent.click(await screen.findByRole('button', { name: 'Preview Chapter 2 Outline' }))

    await waitFor(() => {
      expect(useStore.getState().previewTarget).toEqual({
        type: 'output',
        id: 'out-1',
        title: 'Chapter 2 Outline',
      })
    })
    expect(screen.getByTestId('preview-tab-panel')).toBeInTheDocument()
    expect(screen.getByText('Chapter 2 Outline')).toBeInTheDocument()
  })

  it('shows a top-level Preview tab with empty and selected-target states', () => {
    const { unmount } = render(<RightInspector />)

    fireEvent.click(screen.getByRole('button', { name: 'Preview' }))

    expect(screen.getByTestId('preview-tab-panel')).toBeInTheDocument()
    expect(screen.getByText('Select an item to preview')).toBeInTheDocument()
    unmount()

    useStore.setState({
      previewTarget: { type: 'document', id: 'doc-1', title: 'Research Brief.pdf' },
    })
    previewApiMock.get.mockResolvedValue({
      type: 'document',
      id: 'doc-1',
      title: 'Research Brief.pdf',
      content_preview: 'Document preview text',
      metadata: {},
      links: [],
    })

    render(<RightInspector />)

    expect(screen.getByTestId('preview-tab-panel')).toBeInTheDocument()
    return waitFor(() => {
      expect(screen.getByText('Research Brief.pdf')).toBeInTheDocument()
    })
  })
})
