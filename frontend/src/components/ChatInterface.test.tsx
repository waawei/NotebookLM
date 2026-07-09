import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import { useStore } from '../store/useStore'
import ChatInterface from './ChatInterface'

describe('ChatInterface workspace layout', () => {
  beforeEach(() => {
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
})
