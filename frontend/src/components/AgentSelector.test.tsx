import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const skillsApiMock = vi.hoisted(() => ({
  list: vi.fn(),
}))

vi.mock('../services/api', () => ({
  skillsApi: skillsApiMock,
}))

import { useStore } from '../store/useStore'
import AgentSelector from './AgentSelector'

describe('AgentSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    useStore.setState({ selectedAgentId: null })
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
        {
          skill_id: 'quiz_builder',
          name: 'Quiz Builder',
          description: 'Generate review questions.',
          allowed_tools: ['retrieval.search'],
          prompt_template: '',
          output_kind: 'quiz',
        },
      ],
    })
  })

  it('renders default assistant state when no agent is selected', () => {
    skillsApiMock.list.mockImplementationOnce(() => new Promise(() => {}))
    render(<AgentSelector />)

    expect(screen.getByRole('button', { name: /select agent/i })).toHaveTextContent('Default assistant')
  })

  it('loads skill-backed agent profiles and stores the selected agent', async () => {
    render(<AgentSelector />)

    fireEvent.click(screen.getByRole('button', { name: /select agent/i }))

    expect(await screen.findByRole('option', { name: /Paper Planner/i })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('option', { name: /Paper Planner/i }))

    await waitFor(() => {
      expect(useStore.getState().selectedAgentId).toBe('paper_planner')
    })
    expect(screen.getByRole('button', { name: /select agent/i })).toHaveTextContent('Paper Planner')
  })

  it('uses neutral menu styling with a pale active row', async () => {
    useStore.setState({ selectedAgentId: 'quiz_builder' })
    render(<AgentSelector />)

    fireEvent.click(screen.getByRole('button', { name: /select agent/i }))

    const menu = await screen.findByRole('listbox', { name: /agent profiles/i })
    expect(menu).toHaveClass('bg-white')
    expect(menu).toHaveClass('border-[#e2e1de]')

    const activeRow = screen.getByRole('option', { name: /Quiz Builder/i })
    expect(activeRow).toHaveClass('bg-blue-50')
    expect(activeRow).toHaveClass('text-blue-700')
    expect(activeRow).not.toHaveClass('bg-blue-600')
  })
})
