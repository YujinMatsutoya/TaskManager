const API_BASE = "http://localhost:8000";

export async function fetchTasks(status = null) {
  const url = status
    ? `${API_BASE}/tasks?status=${status}`
    : `${API_BASE}/tasks`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch tasks: ${response.statusText}`);
  }
  return response.json();
}

export async function createTask({ title, due_date = null }) {
  const response = await fetch(`${API_BASE}/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, due_date }),
  });
  if (!response.ok) {
    throw new Error(`Failed to create task: ${response.statusText}`);
  }
  return response.json();
}
