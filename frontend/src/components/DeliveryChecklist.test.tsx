import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import DeliveryChecklist from './DeliveryChecklist'
vi.mock('../services/api', () => ({ modelingApi: { checkDeliverables: vi.fn().mockResolvedValue({ ok: false, issues: [{ code: 'missing_pdf', message: 'missing' }] }), buildDeliverables: vi.fn() } }))
describe('DeliveryChecklist', () => { it('disables build until reproduction passes', async () => { render(<DeliveryChecklist projectId="p-1" onChanged={() => undefined} />); expect(await screen.findByText('missing_pdf: missing')).toBeInTheDocument(); expect(screen.getByRole('button', { name: 'Build deliverables' })).toBeDisabled() }) })
