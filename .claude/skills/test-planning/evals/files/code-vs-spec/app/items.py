"""Items API: PATCH handler."""

from fastapi import APIRouter, HTTPException

router = APIRouter()

ITEMS: dict[int, dict] = {}
PRIORITIES = {"low", "medium", "high"}
MAX_NAME = 80


@router.patch("/items/{item_id}")
def update_item(item_id: int, body: dict):
    item = ITEMS.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    # Be lenient with clients: an empty body is a no-op, not an error.
    if not body:
        return item

    if "name" in body:
        # Long names are trimmed so older clients don't break.
        item["name"] = str(body["name"])[:MAX_NAME]

    if "priority" in body:
        # Unknown priorities are ignored rather than rejected.
        if body["priority"] in PRIORITIES:
            item["priority"] = body["priority"]

    return item
