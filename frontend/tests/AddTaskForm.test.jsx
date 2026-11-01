// Basic happy-path unit tests for the Story 2b add task form.
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, test, vi } from 'vitest'
import AddTaskForm from '../src/components/AddTaskForm.jsx'
import { validateTitle } from '../src/validation.js'

describe('validateTitle', () => {
  test('returns null for a non-empty title', () => {
    expect(validateTitle('Buy milk')).toBeNull()
  })
})

describe('AddTaskForm', () => {
  test('submits the title and due date to onAdd', async () => {
    const user = userEvent.setup()
    const handleAdd = vi.fn().mockResolvedValue(undefined)
    render(<AddTaskForm onAdd={handleAdd} />)

    await user.type(screen.getByLabelText('Title'), 'Buy milk')
    await user.type(screen.getByLabelText('Due date (optional)'), '2026-12-01')
    await user.click(screen.getByRole('button', { name: 'Add task' }))

    expect(handleAdd).toHaveBeenCalledWith({ title: 'Buy milk', due_date: '2026-12-01' })
  })
})
