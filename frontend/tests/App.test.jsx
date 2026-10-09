// Unit tests for App's loading/error/success state machine, per the
// Story 2a spec: the effect that calls `fetchTasks(status)` should set
// loading=true immediately, then resolve into either:
//   - success: tasks populated, loading=false, error=null, TaskList renders
//   - failure: error set from the caught exception, loading=false,
//     TaskList does not render
//
// `fetchTasks` (frontend/src/api/tasks.js) is mocked throughout - these are
// unit tests of App's own state logic, not integration tests against a
// real backend.
import { act, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import App from '../src/App.jsx'
import { fetchTasks } from '../src/api/tasks.js'

vi.mock('../src/api/tasks.js', () => ({
  fetchTasks: vi.fn(),
}))

beforeEach(() => {
  fetchTasks.mockReset()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('App state machine', () => {
  test('calls fetchTasks and does not render the task list while the request is in flight', async () => {
    let resolveFetch
    fetchTasks.mockReturnValue(
      new Promise((resolve) => {
        resolveFetch = resolve
      }),
    )

    render(<App />)

    expect(fetchTasks).toHaveBeenCalledTimes(1)

    // ASSUMPTION: loading and the rendered task list are mutually
    // exclusive branches of the same conditional (a common
    // loading/error/success pattern), so while loading is true neither the
    // populated table nor the "No tasks found." empty state should appear.
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
    expect(screen.queryByText('No tasks found.')).not.toBeInTheDocument()

    // Resolve and flush the pending state update so it doesn't leak into
    // (and produce an act() warning in) the next test.
    await act(async () => {
      resolveFetch([])
      await Promise.resolve()
    })
  })

  test('on success, renders the task list populated with the fetched tasks', async () => {
    fetchTasks.mockResolvedValue([
      { id: 1, title: 'Buy milk', status: 'todo', due_date: null, created_at: '2026-01-01T00:00:00Z' },
    ])

    render(<App />)

    await waitFor(() => {
      expect(screen.getByText('Buy milk')).toBeInTheDocument()
    })

    expect(screen.getByRole('table')).toBeInTheDocument()

    // ASSUMPTION: on a successful load there is no lingering error text
    // visible (error state is cleared/null on success).
    expect(screen.queryByText(/error/i)).not.toBeInTheDocument()
  })

  test('on success with zero tasks, renders TaskList\'s empty state rather than nothing', async () => {
    fetchTasks.mockResolvedValue([])

    render(<App />)

    await waitFor(() => {
      expect(screen.getByText('No tasks found.')).toBeInTheDocument()
    })
  })

  test('on failure, does not render the task list and surfaces the error', async () => {
    fetchTasks.mockRejectedValue(new Error('Network error'))

    render(<App />)

    await waitFor(() => {
      expect(fetchTasks).toHaveBeenCalledTimes(1)
    })

    // Give the rejection time to flow through the catch branch.
    await waitFor(() => {
      expect(screen.queryByText('No tasks found.')).not.toBeInTheDocument()
    })

    expect(screen.queryByRole('table')).not.toBeInTheDocument()

    // ASSUMPTION: the caught error is surfaced somewhere in the document as
    // visible text containing the word "error" (case-insensitive). The
    // spec/task description says error is "set from the caught exception"
    // but doesn't specify the exact wording or markup used to display it.
    expect(screen.getByText(/error/i)).toBeInTheDocument()
  })
})
