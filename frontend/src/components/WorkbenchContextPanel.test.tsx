import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const apiMocks = vi.hoisted(() => ({
  chatApi: {
    listConversations: vi.fn(),
    getConversation: vi.fn(),
    deleteConversation: vi.fn(),
  },
  documentApi: { search: vi.fn(), delete: vi.fn() },
  spacesApi: { list: vi.fn() },
  wikiApi: { list: vi.fn() },
}))

vi.mock('../services/api', () => apiMocks)

import { useStore } from '../store/useStore'
import WorkbenchContextPanel from './WorkbenchContextPanel'

describe('WorkbenchContextPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    apiMocks.chatApi.listConversations.mockResolvedValue({
      conversations: [
        {
          conversation_id: 'conv-1',
          title: 'Paper notes',
          updated_at: '2026-07-10T10:00:00',
          message_count: 2,
          latest_message: 'Summarize chapter 2',
        },
      ],
    })
    apiMocks.chatApi.getConversation.mockResolvedValue({
      conversation_id: 'conv-1',
      title: 'Paper notes',
      messages: [{ role: 'user', content: 'Summarize chapter 2' }],
    })
    apiMocks.chatApi.deleteConversation.mockResolvedValue({ message: 'deleted' })
    apiMocks.documentApi.search.mockResolvedValue({ documents: [], total: 0 })
    apiMocks.spacesApi.list.mockResolvedValue({ spaces: [] })
    apiMocks.wikiApi.list.mockResolvedValue({
      pages: [
        {
          page_id: 'wiki-1',
          title: 'Retrieval Notes',
          content: 'Notes',
          source_doc_ids: ['doc-1'],
          created_at: '2026-07-10T10:00:00',
          updated_at: '2026-07-10T10:00:00',
        },
      ],
      total: 1,
    })
    useStore.setState({
      workbenchLeftTab: 'conversations',
      openConversationTabs: [{ conversation_id: null, title: 'New conversation' }],
      activeConversationTabId: 'new',
      selectedWikiPageIds: [],
      messages: [],
      conversationId: null,
      documents: [],
      selectedDocIds: [],
      activeSpaceId: null,
    })
  })

  it('renders neutral tabs for conversations, sources, and knowledge base', () => {
    apiMocks.chatApi.listConversations.mockImplementation(() => new Promise(() => {}))

    render(<WorkbenchContextPanel isCollapsed={false} onToggle={vi.fn()} onUploadClick={vi.fn()} />)

    expect(screen.getByTestId('workbench-context-panel')).toHaveClass('bg-[#f1f0ef]')
    expect(screen.getByRole('button', { name: 'Conversations' })).toHaveClass('bg-blue-50')
    expect(screen.getByRole('button', { name: 'Conversations' })).not.toHaveClass('bg-blue-600')
    expect(screen.getByRole('button', { name: 'Sources' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Knowledge Base' })).toBeInTheDocument()
  })

  it('reuses source management inside the Sources tab', async () => {
    render(<WorkbenchContextPanel isCollapsed={false} onToggle={vi.fn()} onUploadClick={vi.fn()} />)

    fireEvent.click(screen.getByRole('button', { name: 'Sources' }))

    expect(await screen.findByRole('button', { name: /Add source/i })).toHaveClass('bg-blue-600')
  })

  it('loads conversations and opens a persisted conversation tab', async () => {
    render(<WorkbenchContextPanel isCollapsed={false} onToggle={vi.fn()} onUploadClick={vi.fn()} />)

    expect(await screen.findByTestId('conversation-list')).toBeInTheDocument()
    fireEvent.click(await screen.findByRole('button', { name: /Open Paper notes/i }))

    await waitFor(() => expect(apiMocks.chatApi.getConversation).toHaveBeenCalledWith('conv-1'))
    expect(useStore.getState().conversationId).toBe('conv-1')
    expect(useStore.getState().openConversationTabs).toContainEqual({ conversation_id: 'conv-1', title: 'Paper notes' })
    expect(useStore.getState().messages).toEqual([{ role: 'user', content: 'Summarize chapter 2' }])
  })

  it('deletes conversations and removes the row after success', async () => {
    render(<WorkbenchContextPanel isCollapsed={false} onToggle={vi.fn()} onUploadClick={vi.fn()} />)

    expect(await screen.findByText('Paper notes')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Delete Paper notes/i }))

    await waitFor(() => expect(apiMocks.chatApi.deleteConversation).toHaveBeenCalledWith('conv-1'))
    expect(screen.queryByText('Paper notes')).not.toBeInTheDocument()
  })

  it('reloads the conversation list from the toolbar control', async () => {
    render(<WorkbenchContextPanel isCollapsed={false} onToggle={vi.fn()} onUploadClick={vi.fn()} />)

    expect(await screen.findByText('Paper notes')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Reload conversations' }))

    await waitFor(() => expect(apiMocks.chatApi.listConversations).toHaveBeenCalledTimes(2))
  })

  it('lists knowledge base pages and toggles wiki context', async () => {
    render(<WorkbenchContextPanel isCollapsed={false} onToggle={vi.fn()} onUploadClick={vi.fn()} />)

    fireEvent.click(screen.getByRole('button', { name: 'Knowledge Base' }))

    expect(await screen.findByTestId('kb-context-list')).toBeInTheDocument()
    fireEvent.click(await screen.findByRole('checkbox', { name: /Use Retrieval Notes/i }))

    expect(useStore.getState().selectedWikiPageIds).toEqual(['wiki-1'])
  })
})
