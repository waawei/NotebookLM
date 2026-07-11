import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import ReviewIssuesPanel from './ReviewIssuesPanel'

describe('ReviewIssuesPanel', () => {
  it('shows blocking review issue', () => {
    render(<ReviewIssuesPanel claims={[]} review={{ status: 'failed', issues: [{ severity: 'blocking', code: 'missing', message: 'Missing metric', location: 'Results', artifact_ids: [] }] }} />)
    expect(screen.getByText('Missing metric')).toBeInTheDocument()
  })
})
