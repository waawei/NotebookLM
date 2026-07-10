import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const skillsApiMock = vi.hoisted(() => ({
  list: vi.fn(),
}))

vi.mock('../services/api', () => ({
  skillsApi: skillsApiMock,
}))

import { useStore } from '../store/useStore'
import WorkspaceToolsPanel from './WorkspaceToolsPanel'

describe('WorkspaceToolsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useStore.setState({ pendingSkillCommand: null })
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
  })

  it('renders neutral Tools and Skills sections', async () => {
    render(<WorkspaceToolsPanel />)

    expect(screen.getByRole('heading', { name: 'Tools' })).toBeInTheDocument()
    expect(screen.getByText('Mind map')).toBeInTheDocument()
    expect(screen.getByText('Quiz')).toBeInTheDocument()
    expect(screen.getByText('Flashcards')).toBeInTheDocument()
    expect(screen.getByText('Research brief')).toBeInTheDocument()
    expect(screen.getByText('Paper outline')).toBeInTheDocument()

    expect(await screen.findByRole('heading', { name: 'Skills' })).toBeInTheDocument()
    expect(screen.getByText('Paper Planner')).toBeInTheDocument()
    expect(screen.getByText('Build a paper outline from selected sources.')).toBeInTheDocument()
    expect(screen.getByText('outline')).toBeInTheDocument()

    const card = screen.getByTestId('workspace-skill-card-paper_planner')
    expect(card).toHaveClass('bg-white')
    expect(card).toHaveClass('border-[#e2e1de]')
    expect(card).not.toHaveClass('bg-blue-600')
  })

  it('clicking a skill card prepares a composer slash command', async () => {
    render(<WorkspaceToolsPanel />)

    fireEvent.click(await screen.findByTestId('workspace-skill-card-paper_planner'))

    expect(useStore.getState().pendingSkillCommand).toEqual({
      skill_id: 'paper_planner',
      text: '/paper_planner ',
    })
  })
})
