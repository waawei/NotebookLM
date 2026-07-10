import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const skillsApiMock = vi.hoisted(() => ({
  list: vi.fn(),
}))

vi.mock('../services/api', () => ({
  skillsApi: skillsApiMock,
}))

import SlashCommandMenu from './SlashCommandMenu'

describe('SlashCommandMenu', () => {
  const skills = [
    {
      skill_id: 'paper_planner',
      name: 'Paper Planner',
      description: 'Build a paper outline.',
      allowed_tools: ['retrieval.search'],
      prompt_template: '',
      output_kind: 'outline',
    },
    {
      skill_id: 'quiz_builder',
      name: 'Quiz Builder',
      description: 'Generate review questions.',
      allowed_tools: ['retrieval.search'],
      prompt_template: '',
      output_kind: 'quiz',
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    skillsApiMock.list.mockResolvedValue({ skills })
  })

  it('renders slash command rows and filters by typed query', async () => {
    render(<SlashCommandMenu query="/paper" onSelect={vi.fn()} onClose={vi.fn()} />)

    expect(await screen.findByRole('option', { name: /\/paper_planner/i })).toBeInTheDocument()
    expect(screen.queryByRole('option', { name: /\/quiz_builder/i })).not.toBeInTheDocument()
  })

  it('moves highlight with arrow keys and selects highlighted skill with enter', async () => {
    const onSelect = vi.fn()
    render(<SlashCommandMenu query="/" onSelect={onSelect} onClose={vi.fn()} />)

    const listbox = await screen.findByRole('listbox', { name: /skill commands/i })
    fireEvent.keyDown(listbox, { key: 'ArrowDown' })
    fireEvent.keyDown(listbox, { key: 'Enter' })

    await waitFor(() => {
      expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ skill_id: 'quiz_builder' }))
    })
  })

  it('closes on escape without selecting a skill', async () => {
    const onSelect = vi.fn()
    const onClose = vi.fn()
    render(<SlashCommandMenu query="/" onSelect={onSelect} onClose={onClose} />)

    const listbox = await screen.findByRole('listbox', { name: /skill commands/i })
    fireEvent.keyDown(listbox, { key: 'Escape' })

    expect(onClose).toHaveBeenCalled()
    expect(onSelect).not.toHaveBeenCalled()
  })
})
