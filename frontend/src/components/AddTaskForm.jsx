import { useState } from "react";
import { validateTitle } from "../validation";

export default function AddTaskForm({ onAdd }) {
  const [title, setTitle] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationError = validateTitle(title);
    if (validationError) {
      setError(validationError);
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await onAdd({ title: title.trim(), due_date: dueDate || null });
      setTitle("");
      setDueDate("");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="add-task-form" onSubmit={handleSubmit} noValidate>
      <label htmlFor="task-title">Title</label>
      <input
        id="task-title"
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />

      <label htmlFor="task-due-date">Due date (optional)</label>
      <input
        id="task-due-date"
        type="date"
        value={dueDate}
        onChange={(e) => setDueDate(e.target.value)}
      />

      <button type="submit" disabled={submitting}>
        Add task
      </button>

      {error && (
        <p role="alert" style={{ color: "red" }}>
          {error}
        </p>
      )}
    </form>
  );
}
