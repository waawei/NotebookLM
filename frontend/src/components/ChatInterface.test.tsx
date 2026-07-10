import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { act } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const chatApiMock = vi.hoisted(() => ({
  createStreamRequest: vi.fn(),
  suggestQuestions: vi.fn(),
}))
const agentsApiMock = vi.hoisted(() => ({
  createRun: vi.fn(),
}))
const skillsApiMock = vi.hoisted(() => ({
  list: vi.fn(),
}))
const wikiApiMock = vi.hoisted(() => ({
  list: vi.fn(),
}))

vi.mock('../services/api', () => ({
  chatApi: chatApiMock,
  agentsApi: agentsApiMock,
  skillsApi: skillsApiMock,
  noteApi: { createFromMessage: vi.fn() },
  wikiApi: wikiApiMock,
}))
import { useStore } from '../store/useStore'
import ChatInterface from './ChatInterface'

describe('ChatInterface workspace layout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    Element.prototype.scrollIntoView = vi.fn()
    chatApiMock.suggestQuestions.mockResolvedValue({ questions: [] })
    agentsApiMock.createRun.mockResolvedValue({
      run_id: 'run-1',
      skill_id: 'paper_planner',
      status: 'running',
      input_payload: { doc_ids: ['doc-1'], request: 'outline chapter 2' },
      output_id: null,
      error: null,
      steps: [],
    })
    skillsApiMock.list.mockImplementation(() => new Promise(() => {}))
    wikiApiMock.list.mockImplementation(() => new Promise(() => {}))
    useStore.setState({
      messages: [],
      selectedDocIds: [],
      conversationId: null,
      isLoading: false,
      suggestedQuestions: [],
      documents: [],
      selectedWikiPageIds: [],
      openConversationTabs: [{ conversation_id: null, title: 'New conversation' }],
      activeConversationTabId: 'new',
      selectedAgentId: null,
      pendingSkillCommand: null,
      artifactRefreshToken: 0,
    })
  })

  it('uses a continuous message timeline with a bottom composer', () => {
    render(<ChatInterface />)

    expect(screen.getByTestId('message-timeline')).toHaveClass('flex-1')
    expect(screen.getByTestId('chat-composer')).toHaveClass('sticky')
    expect(screen.getByText('Selected sources: 0')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /select agent/i })).toHaveTextContent('Default assistant')
  })

  it('uses a neutral Reviva-style chat chrome without broad blue surfaces', () => {
    render(<ChatInterface />)

    expect(screen.getByTestId('conversation-tab-strip')).toHaveClass('bg-[#f8f7f6]')
    expect(screen.getByRole('button', { name: 'New conversation' })).toBeInTheDocument()

    const emptyIcon = screen.getByTestId('empty-state-icon')
    expect(emptyIcon).toHaveClass('bg-blue-50')
    expect(emptyIcon).not.toHaveClass('bg-gradient-to-br')

    const activeModeTab = screen.getByRole('button', { name: 'Knowledge Base' })
    expect(activeModeTab).toHaveClass('bg-blue-50')
    expect(activeModeTab).toHaveClass('text-blue-700')
    expect(activeModeTab).not.toHaveClass('bg-blue-600')
    expect(activeModeTab).not.toHaveClass('text-white')

    const composerFrame = screen.getByTestId('composer-frame')
    expect(composerFrame).toHaveClass('rounded-xl')
    expect(composerFrame).toHaveClass('border')
    expect(composerFrame).not.toHaveClass('border-2')
    expect(composerFrame).not.toHaveClass('shadow-xl')
  })

  it('shows selected source and wiki context above the composer', async () => {
    wikiApiMock.list.mockResolvedValue({
      pages: [
        { page_id: 'wiki-1', title: 'Retrieval Notes', content: '', source_doc_ids: [], created_at: '2026-07-10T00:00:00', updated_at: '2026-07-10T00:00:00' },
      ],
      total: 1,
    })
    useStore.setState({
      documents: [
        { doc_id: 'doc-1', filename: 'Research Brief.pdf', file_type: 'pdf', upload_time: '2026-07-10T00:00:00', status: 'completed', total_chunks: 3 },
      ],
      selectedDocIds: ['doc-1'],
      selectedWikiPageIds: ['wiki-1'],
    })

    render(<ChatInterface />)

    expect(screen.getByText('Research Brief.pdf')).toBeInTheDocument()
    expect(await screen.findByText('Retrieval Notes')).toBeInTheDocument()
  })

  it('uses neutral workbench surfaces for messages and citations', () => {
    useStore.setState({
      messages: [
        { role: 'user', content: 'Compare these two sections.' },
        {
          role: 'assistant',
          content: 'The second section narrows the claim.',
          citations: [
            {
              number: 1,
              doc_id: 'doc-1',
              doc_name: 'Research Brief.pdf',
              page: 4,
              chunk_id: 2,
              content: 'The cited passage supports the narrowed claim.',
              relevance_score: 0.92,
            },
          ],
        },
      ],
    })

    render(<ChatInterface />)

    const userBubble = screen.getByText('Compare these two sections.').closest('[data-message-role="user"]')
    expect(userBubble).toHaveClass('bg-slate-100')
    expect(userBubble).toHaveClass('text-slate-900')
    expect(userBubble).not.toHaveClass('bg-blue-600')
    expect(userBubble).not.toHaveClass('text-white')

    const assistantPaper = screen.getByText('The second section narrows the claim.').closest('[data-message-role="assistant"]')
    expect(assistantPaper).toHaveClass('bg-white')
    expect(assistantPaper).toHaveClass('border-slate-200')

    const citationCard = screen.getByText('Research Brief.pdf').closest('[data-testid="citation-card"]')
    expect(citationCard).toHaveClass('bg-white')
    expect(citationCard).toHaveClass('border-slate-200')
    expect(citationCard).not.toHaveClass('bg-blue-50')

    expect(screen.getByText('1')).toHaveClass('bg-blue-600')
  })

  it('shows an inline source-selection recovery message without calling the chat API', async () => {
    render(<ChatInterface />)

    fireEvent.change(screen.getByPlaceholderText('Ask a question about your sources...'), { target: { value: 'Question' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send message' }))

    expect(await screen.findByText('Select at least one source before asking a question.')).toBeInTheDocument()
    expect(chatApiMock.createStreamRequest).not.toHaveBeenCalled()
  })

  it('opens a slash command menu and inserts the selected skill command', async () => {
    skillsApiMock.list.mockResolvedValue({
      skills: [
        {
          skill_id: 'paper_planner',
          name: 'Paper Planner',
          description: 'Build a paper outline from selected sources.',
          allowed_tools: ['retrieval.search'],
          prompt_template: '',
          output_kind: 'outline',
        },
      ],
    })
    render(<ChatInterface />)

    fireEvent.change(screen.getByPlaceholderText('Ask a question about your sources...'), { target: { value: '/' } })

    expect(await screen.findByRole('listbox', { name: /skill commands/i })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('option', { name: /\/paper_planner/i }))

    expect(screen.getByPlaceholderText('Ask a question about your sources...')).toHaveValue('/paper_planner ')
    expect(useStore.getState().pendingSkillCommand).toEqual({
      skill_id: 'paper_planner',
      text: '/paper_planner ',
    })
  })

  it('fills the composer when a workspace skill card prepares a command', async () => {
    render(<ChatInterface />)

    act(() => {
      useStore.getState().setPendingSkillCommand({ skill_id: 'paper_planner', text: '/paper_planner ' })
    })

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Ask a question about your sources...')).toHaveValue('/paper_planner ')
    })
  })

  it('submits a skill command through the inspectable agent run API', async () => {
    useStore.setState({ selectedDocIds: ['doc-1'] })
    render(<ChatInterface />)

    fireEvent.change(screen.getByPlaceholderText('Ask a question about your sources...'), {
      target: { value: '/paper_planner outline chapter 2' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Send message' }))

    await waitFor(() => {
      expect(agentsApiMock.createRun).toHaveBeenCalledWith({
        skill_id: 'paper_planner',
        doc_ids: ['doc-1'],
        request: 'outline chapter 2',
      })
    })
    expect(chatApiMock.createStreamRequest).not.toHaveBeenCalled()
    expect(await screen.findByText('Agent run started')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Open Agents' })).toBeInTheDocument()
    expect(useStore.getState().artifactRefreshToken).toBe(1)
  })

  it('blocks skill command execution without selected sources', async () => {
    render(<ChatInterface />)

    fireEvent.change(screen.getByPlaceholderText('Ask a question about your sources...'), {
      target: { value: '/paper_planner outline chapter 2' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Send message' }))

    expect(await screen.findByText('Select at least one source before running a skill.')).toBeInTheDocument()
    expect(agentsApiMock.createRun).not.toHaveBeenCalled()
    expect(chatApiMock.createStreamRequest).not.toHaveBeenCalled()
  })

  it('shows a recoverable skill run error without hiding the failure', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
    agentsApiMock.createRun.mockRejectedValue(new Error('backend unavailable'))
    useStore.setState({ selectedDocIds: ['doc-1'] })
    render(<ChatInterface />)

    fireEvent.change(screen.getByPlaceholderText('Ask a question about your sources...'), {
      target: { value: '/paper_planner outline chapter 2' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Send message' }))

    expect(await screen.findByText('Agent run failed. Review the request and try again.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Open Agents' })).toBeInTheDocument()
    consoleError.mockRestore()
  })

  it('replaces an optimistic assistant reply with a safe failure and local details', async () => {
    const diagnostic = {
      phase: 'chat_completion',
      status_code: 429,
      category: 'rate_limited',
      summary: 'The upstream request was rate limited.',
    }
    const encoder = new TextEncoder()
    chatApiMock.createStreamRequest.mockResolvedValue({
      body: new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'error', message: 'The response could not be generated. Check the LLM connection in Settings and try again.', diagnostic })}\n\n`))
          controller.close()
        },
      }),
    })
    useStore.setState({ selectedDocIds: ['doc-1'] })
    render(<ChatInterface />)

    fireEvent.change(screen.getByPlaceholderText('Ask a question about your sources...'), { target: { value: 'Question' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send message' }))

    expect(await screen.findByText('The response could not be generated. Check the LLM connection in Settings and try again.')).toBeInTheDocument()
    expect(screen.getByText('Connection details')).toBeInTheDocument()
    expect(screen.queryByText('Thinking...')).not.toBeInTheDocument()
  })
})
