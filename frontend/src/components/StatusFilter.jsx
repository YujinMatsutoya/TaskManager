export default function StatusFilter({ selectedStatus, onChange }) {
  return (
    <div>
      <label htmlFor="status-filter">Filter by status:</label>
      <select
        id="status-filter"
        value={selectedStatus || ""}
        onChange={(e) => onChange(e.target.value || null)}
      >
        <option value="">All</option>
        <option value="todo">todo</option>
        <option value="in_progress">in_progress</option>
        <option value="done">done</option>
      </select>
    </div>
  );
}
