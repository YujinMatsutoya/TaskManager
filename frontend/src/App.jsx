import { useState, useEffect } from "react";
import { fetchTasks, createTask } from "./api/tasks";
import TaskList from "./components/TaskList";
import StatusFilter from "./components/StatusFilter";
import AddTaskForm from "./components/AddTaskForm";
import "./App.css";

export default function App() {
  const [status, setStatus] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const loadTasks = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchTasks(status);
        setTasks(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadTasks();
  }, [status, refreshKey]);

  const handleAdd = async (task) => {
    await createTask(task);
    setRefreshKey((key) => key + 1);
  };

  return (
    <div className="app">
      <h1>Task Manager</h1>
      <AddTaskForm onAdd={handleAdd} />
      <StatusFilter selectedStatus={status} onChange={setStatus} />

      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "red" }}>Error: {error}</p>}
      {!loading && !error && <TaskList tasks={tasks} />}
    </div>
  );
}
