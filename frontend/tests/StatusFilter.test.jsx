// Unit tests for StatusFilter's null <-> "" conversion, per the Story 2a
// spec: `selectedStatus` of `null` should display as the empty ("All")
// option, and selecting that empty option should report back `null` (not
// ""), while selecting a real status reports that status string.
//
// ASSUMPTION: the <select> exposes an "All" option with value="" plus one
// option per status enum value from Task_Manager_Spec.md (`todo`,
// `in_progress`, `done`). The spec fixes the status enum but doesn't spell
// out StatusFilter's exact option markup/labels, so these tests interact
// with the select purely via its role and option values, never by label
// text, to stay resilient to label wording.
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, test, vi } from 'vitest'
import StatusFilter from '../src/components/StatusFilter.jsx'

describe('StatusFilter', () => {
  test('a null selectedStatus renders the select with the empty ("All") option selected', () => {
    render(<StatusFilter selectedStatus={null} onChange={vi.fn()} />)

    const select = screen.getByRole('combobox')
    expect(select).toHaveValue('')
  })

  test('a real selectedStatus renders the select with that value selected', () => {
    render(<StatusFilter selectedStatus="todo" onChange={vi.fn()} />)

    const select = screen.getByRole('combobox')
    expect(select).toHaveValue('todo')
  })

  test('selecting the "All" option calls onChange with null, not ""', async () => {
    const user = userEvent.setup()
    const handleChange = vi.fn()
    render(<StatusFilter selectedStatus="todo" onChange={handleChange} />)

    const select = screen.getByRole('combobox')
    await user.selectOptions(select, '')

    expect(handleChange).toHaveBeenCalledTimes(1)
    expect(handleChange).toHaveBeenCalledWith(null)
  })

  test('selecting a real status value calls onChange with that string', async () => {
    const user = userEvent.setup()
    const handleChange = vi.fn()
    render(<StatusFilter selectedStatus={null} onChange={handleChange} />)

    const select = screen.getByRole('combobox')
    await user.selectOptions(select, 'todo')

    expect(handleChange).toHaveBeenCalledTimes(1)
    expect(handleChange).toHaveBeenCalledWith('todo')
  })
})
