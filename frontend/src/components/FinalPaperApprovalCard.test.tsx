import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import FinalPaperApprovalCard from './FinalPaperApprovalCard'

describe('FinalPaperApprovalCard', () => {
  it('disables final approval for blocking review', () => {
    render(<FinalPaperApprovalCard projectId="p-1" review={{ status: 'failed', issues: [{ severity: 'blocking', code: 'missing', message: 'Missing metric', location: 'Results', artifact_ids: [] }] }} onChanged={() => undefined} />)
    expect(screen.getByRole('button', { name: 'Request final approval' })).toBeDisabled()
  })
})
