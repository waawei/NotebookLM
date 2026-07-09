import { beforeEach, describe, expect, it } from 'vitest'
import { resolveTheme, useStore } from './useStore'

describe('theme preference', () => {
  beforeEach(() => {
    localStorage.clear()
    useStore.setState({ theme: 'system' })
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
