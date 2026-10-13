# Items API: spec (v1.2, approved)

## Item
| Field | Type | Rules |
|---|---|---|
| `id` | int | assigned by the server |
| `name` | string | required, 1–80 characters |
| `priority` | enum `low` / `medium` / `high` | default `medium` |

## PATCH /items/{id}
This is a partial update: only the fields sent are changed.
- Unknown `priority` values (e.g. `"urgent"`) are rejected with **422**, and the item is not changed.
- An empty body `{}` is rejected with **422**.
- A `name` longer than 80 characters is rejected with **422**. It is never silently shortened.
- An unknown `id` returns **404**.
- On success it returns **200** with the full updated item.
