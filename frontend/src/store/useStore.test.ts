import { beforeEach, describe, expect, it } from 'vitest'
import { resolveTheme, useStore } from './useStore'

describe('theme preference', () => {
  beforeEach(() => {
    localStorage.clear()
    useStore.setState({
      theme: 'system',
      workbenchLeftTab: 'conversations',
      openConversationTabs: [{ conversation_id: null, title: 'New conversation' }],
      activeConversationTabId: 'new',
      previewTarget: null,
      selectedWikiPageIds: [],
    })
  })

  it('stores an explicit theme preference without storing configuration values', () => {
    useStore.getState().setTheme('dark')

    expect(useStore.getState().theme).toBe('dark')
    expect(localStorage.getItem('theme_preference')).toBe('dark')
    expect(localStorage.getItem('llm_api_key')).toBeNull()
  })

  it('uses system color only for the system preference', () => {
    expect(resolveTheme('system', true)).toBe('dark')
    expect(resolveTheme('system', false)).toBe('light')
    expect(resolveTheme('light', true)).toBe('light')
  })
})

describe('language preference', () => {
  beforeEach(() => {
    localStorage.clear()
    useStore.setState({ language: 'en' })
  })

  it('stores an explicit language preference without storing configuration values', () => {
    useStore.getState().setLanguage('zh-CN')

    expect(useStore.getState().language).toBe('zh-CN')
    expect(localStorage.getItem('language_preference')).toBe('zh-CN')
    expect(localStorage.getItem('llm_api_key')).toBeNull()
  })
})

describe('workbench information architecture state', () => {
  beforeEach(() => {
    localStorage.clear()
    useStore.setState({
      workbenchLeftTab: 'conversations',
      openConversationTabs: [{ conversation_id: null, title: 'New conversation' }],
      activeConversationTabId: 'new',
      previewTarget: null,
      selectedWikiPageIds: [],
      messages: [],
      conversationId: null,
    })
  })

  it('defaults the left panel to conversations', () => {
    expect(useStore.getState().workbenchLeftTab).toBe('conversations')
  })

  it('opens conversation tabs without duplicating existing conversations', () => {
    useStore.getState().openConversationTab({ conversation_id: 'conv-1', title: 'Paper notes' })
    useStore.getState().openConversationTab({ conversation_id: 'conv-1', title: 'Paper notes' })

    expect(useStore.getState().openConversationTabs).toEqual([
      { conversation_id: null, title: 'New conversation' },
      { conversation_id: 'conv-1', title: 'Paper notes' },
    ])
    expect(useStore.getState().activeConversationTabId).toBe('conv-1')
    expect(JSON.parse(localStorage.getItem('open_conversation_tabs') || '[]')).toHaveLength(2)
  })

  it('closing the active tab selects the nearest tab and falls back to new chat', () => {
    useStore.getState().openConversationTab({ conversation_id: 'conv-1', title: 'Paper notes' })
    useStore.getState().openConversationTab({ conversation_id: 'conv-2', title: 'Review notes' })

    useStore.getState().closeConversationTab('conv-2')
    expect(useStore.getState().activeConversationTabId).toBe('conv-1')

    useStore.getState().closeConversationTab('conv-1')
    expect(useStore.getState().openConversationTabs).toEqual([{ conversation_id: null, title: 'New conversation' }])
    expect(useStore.getState().activeConversationTabId).toBe('new')
  })

  it('stores preview targets only in session state', () => {
    useStore.getState().setPreviewTarget({ type: 'document', id: 'doc-1', title: 'Research Brief.pdf' })

    expect(useStore.getState().previewTarget).toEqual({ type: 'document', id: 'doc-1', title: 'Research Brief.pdf' })
    expect(localStorage.getItem('preview_target')).toBeNull()

    useStore.getState().setPreviewTarget(null)
    expect(useStore.getState().previewTarget).toBeNull()
  })

  it('toggles wiki context without duplicates and persists selected ids', () => {
    useStore.getState().toggleWikiContext('wiki-1')
    useStore.getState().toggleWikiContext('wiki-1')
    useStore.getState().toggleWikiContext('wiki-2')

    expect(useStore.getState().selectedWikiPageIds).toEqual(['wiki-2'])
    expect(JSON.parse(localStorage.getItem('selected_wiki_page_ids') || '[]')).toEqual(['wiki-2'])
  })
})

describe('workbench agent and artifact state', () => {
  beforeEach(() => {
    localStorage.clear()
    useStore.setState({
      selectedAgentId: null,
      pendingSkillCommand: null,
      artifactRefreshToken: 0,
    })
  })

  it('persists the selected agent id through local storage', () => {
    useStore.getState().setSelectedAgentId('paper_planner')

    expect(useStore.getState().selectedAgentId).toBe('paper_planner')
    expect(localStorage.getItem('selected_agent_id')).toBe('paper_planner')
  })

  it('stores and clears a pending slash skill command without persisting it', () => {
    useStore.getState().setPendingSkillCommand({ skill_id: 'paper_planner', text: '/paper_planner ' })

    expect(useStore.getState().pendingSkillCommand).toEqual({
      skill_id: 'paper_planner',
      text: '/paper_planner ',
    })
    expect(localStorage.getItem('pending_skill_command')).toBeNull()

    useStore.getState().clearPendingSkillCommand()

    expect(useStore.getState().pendingSkillCommand).toBeNull()
  })

  it('increments the artifact refresh token monotonically', () => {
    useStore.getState().bumpArtifactRefreshToken()
    useStore.getState().bumpArtifactRefreshToken()

    expect(useStore.getState().artifactRefreshToken).toBe(2)
  })
})

describe('modeling project selection', () => {
  beforeEach(() => {
    localStorage.clear()
    useStore.setState({ selectedModelingProjectId: null })
  })

  it('persists the selected modeling project id', () => {
    useStore.getState().setSelectedModelingProjectId('project-1')

    expect(useStore.getState().selectedModelingProjectId).toBe('project-1')
    expect(localStorage.getItem('selected_modeling_project_id')).toBe('project-1')

    useStore.getState().setSelectedModelingProjectId(null)
    expect(localStorage.getItem('selected_modeling_project_id')).toBeNull()
  })
})
