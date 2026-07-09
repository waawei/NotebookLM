import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const chatApiMock = vi.hoisted(() => ({
  createStreamRequest: vi.fn(),
  suggestQuestions: vi.fn(),
}))

vi.mock('../services/api', () => ({
  chatApi: chatApiMock,
  noteApi: { createFromMessage: vi.fn() },
}))
import { useStore } from '../store/useStore'
import ChatInterface from './ChatInterface'

describe('ChatInterface workspace layout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    Element.prototype.scrollIntoView = vi.fn()
    chatApiMock.suggestQuestions.mockResolvedValue({ questions: [] })
    useStore.setState({
      messages: [],
      selectedDocIds: [],
      conversationId: null,
      isLoading: false,
      suggestedQuestions: [],
    })
  })

  it('uses a continuous message timeline with a bottom composer', () => {
    render(<ChatInterface />)

    expect(screen.getByTestId('message-timeline')).toHaveClass('flex-1')
    expect(screen.getByTestId('chat-composer')).toHaveClass('sticky')
    expect(screen.getByText('Selected sources: 0')).toBeInTheDocument()
  })

  it('shows an inline source-selection recovery message without calling the chat API', async () => {
    render(<ChatInterface />)

    fireEvent.change(screen.getByPlaceholderText('Ask a question about your sources...'), { target: { value: 'Question' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send message' }))

    expect(await screen.findByText('Select at least one source before asking a question.')).toBeInTheDocument()
    expect(chatApiMock.createStreamRequest).not.toHaveBeenCalled()
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
