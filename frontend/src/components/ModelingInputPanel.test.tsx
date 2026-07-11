import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const modelingApiMock = vi.hoisted(() => ({ uploadInput: vi.fn() }))
vi.mock('../services/api', () => ({ modelingApi: modelingApiMock }))

import ModelingInputPanel from './ModelingInputPanel'

describe('ModelingInputPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    modelingApiMock.uploadInput.mockResolvedValue({ artifact_id: 'input-1' })
  })

  it('uploads problem and CSV files through separate immutable input actions', async () => {
    const changed = vi.fn()
    render(<ModelingInputPanel projectId="project-1" onChanged={changed} />)
    const problem = new File(['预测销量'], '赛题.txt', { type: 'text/plain' })
    const data = new File(['x,y\n1,2\n'], 'train.csv', { type: 'text/csv' })

    fireEvent.change(screen.getByLabelText('Problem file'), { target: { files: [problem] } })
    fireEvent.click(screen.getByRole('button', { name: 'Upload problem' }))
    await waitFor(() => expect(modelingApiMock.uploadInput).toHaveBeenCalledWith('project-1', 'problem', problem))

    fireEvent.change(screen.getByLabelText('CSV data file'), { target: { files: [data] } })
    fireEvent.click(screen.getByRole('button', { name: 'Upload data' }))
    await waitFor(() => expect(modelingApiMock.uploadInput).toHaveBeenCalledWith('project-1', 'data', data))
    expect(changed).toHaveBeenCalledTimes(2)
  })

  it('shows an upload failure without clearing the selected action', async () => {
    modelingApiMock.uploadInput.mockRejectedValue(new Error('duplicate'))
    render(<ModelingInputPanel projectId="project-1" onChanged={() => undefined} />)
    const data = new File(['x\n1\n'], 'train.csv', { type: 'text/csv' })
    fireEvent.change(screen.getByLabelText('CSV data file'), { target: { files: [data] } })
    fireEvent.click(screen.getByRole('button', { name: 'Upload data' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to upload data input.')
  })
})
