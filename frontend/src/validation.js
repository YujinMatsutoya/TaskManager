export function validateTitle(title) {
  return title.trim() ? null : "Title is required";
}
