┌─────────────────┐
│  Browser / curl  │   "hey, GET /tasks"
└────────┬─────────┘
         │  raw HTTP over the network
         ▼
┌──────────────────────────────┐
│           Uvicorn             │   the actual server process
│  listens on localhost:8000,   │   parses raw HTTP into something
│  speaks the HTTP protocol     │   Python can work with
└────────┬──────────────────────┘
         │  hands off the parsed request
         ▼
┌──────────────────────────────┐
│           FastAPI              │   matches the URL + method to
│   (the `app` object)           │   the right function, e.g.
│   routes to the right          │   @app.get("/tasks")
│   handler in main.py           │
└────────┬──────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│   Route handler (main.py)      │   e.g. list_tasks(status, db)
│   validates in/out shape       │◄── schemas.py (TaskCreate/
│   via Pydantic schemas         │     TaskUpdate/TaskRead)
└────────┬──────────────────────┘
         │  calls into
         ▼
┌──────────────────────────────┐
│         crud.py                │   the actual DB logic:
│   create_task / get_tasks /    │   builds queries, adds/updates
│   update_task / delete_task    │   objects, calls db.commit()
└────────┬──────────────────────┘
         │  uses a session from
         ▼
┌──────────────────────────────┐
│       database.py               │   SessionLocal → engine
│   engine + SessionLocal         │   translates Python objects
│   (get_db() hands out           │   into actual SQL
│   one session per request)      │
└────────┬──────────────────────┘
         │  SQL
         ▼
┌──────────────────────────────┐
│         tasks.db                │   the SQLite file on disk
│   (the Task table, per          │
│   models.py)                    │
└──────────────────────────────┘
