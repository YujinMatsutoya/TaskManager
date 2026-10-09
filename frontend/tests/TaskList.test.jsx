// Unit tests for TaskList's empty-vs-non-empty branch and its due_date
// fallback rendering, per the Story 2a spec.
//
// Deliberately NOT tested here: created_at formatting (`.toLocaleString()`)
// - that's a framework/locale pass-through, not app logic, per the task
// scope for this pass.
import { render, screen, within } from '@testing-library/react'
import { describe, expect, test } from 'vitest'
import TaskList from '../src/components/TaskList.jsx'

const baseTask = {
  status: 'todo',
  created_at: '2026-01-01T00:00:00Z',
}

describe('TaskList', () => {
  test('renders "No tasks found." when given an empty task list', () => {
    render(<TaskList tasks={[]} />)

    expect(screen.getByText('No tasks found.')).toBeInTheDocument()
  })

  test('renders one table row per task when given a non-empty task list', () => {
    const tasks = [
      { ...baseTask, id: 1, title: 'Buy milk', due_date: '2026-02-01' },
      { ...baseTask, id: 2, title: 'Walk the dog', due_date: '2026-02-02' },
      { ...baseTask, id: 3, title: 'Write report', due_date: '2026-02-03' },
    ]

    render(<TaskList tasks={tasks} />)

    expect(screen.queryByText('No tasks found.')).not.toBeInTheDocument()

    const table = screen.getByRole('table')

    // Every task's title should appear, each inside its own row.
    tasks.forEach((task) => {
      const titleCell = within(table).getByText(task.title)
      expect(titleCell.closest('tr')).not.toBeNull()
    })

    // ASSUMPTION: there is exactly one data row per task (i.e. no task is
    // split across multiple rows, and no extra data rows are injected).
    // Any header row is excluded here by filtering for rows that contain
    // one of the task titles.
    const dataRows = within(table)
      .getAllByRole('row')
      .filter((row) => tasks.some((task) => within(row).queryByText(task.title)))
    expect(dataRows).toHaveLength(tasks.length)
  })

  test('renders "—" as a fallback for a task with a null due_date', () => {
    const tasks = [{ ...baseTask, id: 1, title: 'No due date task', due_date: null }]

    render(<TaskList tasks={tasks} />)

    const row = screen.getByText('No due date task').closest('tr')
    expect(within(row).getByText('—')).toBeInTheDocument()
  })

  test('renders the due_date value as-is for a task that has one', () => {
    // ASSUMPTION: a non-null due_date is rendered verbatim (no reformatting)
    // - the spec/task description only calls out a fallback for the null
    // case, and explicitly excludes date-formatting concerns from this pass.
    const tasks = [{ ...baseTask, id: 1, title: 'Has due date task', due_date: '2026-03-15' }]

    render(<TaskList tasks={tasks} />)

    const row = screen.getByText('Has due date task').closest('tr')
    expect(within(row).getByText('2026-03-15')).toBeInTheDocument()
  })
})
