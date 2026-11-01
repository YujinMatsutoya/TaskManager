// Basic happy-path unit test for createTask; fetch is stubbed.
import { afterEach, describe, expect, test, vi } from 'vitest'
import { createTask } from '../src/api/tasks.js'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('createTask', () => {
  test('POSTs the task to /tasks and returns the created task', async () => {
    const created = { id: 1, title: 'Buy milk', due_date: null, status: 'todo', created_at: '2026-01-01T00:00:00Z' }
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve(created) })
    vi.stubGlobal('fetch', fetchMock)

    const result = await createTask({ title: 'Buy milk' })

    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'Buy milk', due_date: null }),
    })
    expect(result).toEqual(created)
  })
})
