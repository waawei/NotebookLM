import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'

import { useStore } from '../store/useStore'
import ConversationTabStrip from './ConversationTabStrip'

describe('ConversationTabStrip', () => {
  beforeEach(() => {
    localStorage.clear()
    useStore.setState({
      messages: [{ role: 'user', content: 'Existing question' }],
      conversationId: 'conv-1',
      openConversationTabs: [
        { conversation_id: null, title: 'New conversation' },
        { conversation_id: 'conv-1', title: 'Paper notes' },
        { conversation_id: 'conv-2', title: 'Review notes' },
      ],
      activeConversationTabId: 'conv-1',
    })
  })

  it('renders scrollable tabs with pale active state and close controls', () => {
    render(<ConversationTabStrip />)

    expect(screen.getByTestId('conversation-tab-strip')).toHaveClass('overflow-x-auto')
    expect(screen.getByRole('button', { name: 'Paper notes' })).toHaveClass('bg-blue-50')
    expect(screen.getByRole('button', { name: 'Paper notes' })).not.toHaveClass('bg-blue-600')

    fireEvent.click(screen.getByRole('button', { name: /Close Paper notes/i }))

    expect(useStore.getState().openConversationTabs).not.toContainEqual({ conversation_id: 'conv-1', title: 'Paper notes' })
    expect(useStore.getState().activeConversationTabId).toBe('conv-2')
  })

  it('starts a new conversation tab and clears current chat state', () => {
    render(<ConversationTabStrip />)

    fireEvent.click(screen.getByRole('button', { name: 'New conversation' }))

    expect(useStore.getState().activeConversationTabId).toBe('new')
    expect(useStore.getState().conversationId).toBeNull()
    expect(useStore.getState().messages).toEqual([])
  })
})
