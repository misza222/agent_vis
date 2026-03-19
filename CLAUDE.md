# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**See also: [Global Configuration](~/.claude/CLAUDE.md)**

## Project Overview

A workflow visualization tool with a FastAPI backend and vanilla JS frontend. The backend provides REST APIs for workflow CRUD and a WebSocket endpoint for real-time flow animations. The frontend renders workflows on an HTML5 canvas with animated particles flowing along edge paths.

## Commands

```bash
make install   # uv sync
make run       # uv run uvicorn src.agent_vis.app:app --reload
make test      # pytest
make lint      # ruff check .
make format    # ruff format .
make typecheck # mypy src/agent_vis

# Single test
pytest tests/test_api.py::test_function_name

# Demo scripts (server must be running first)
uv run python showcase.py basic
uv run python showcase.py parallel
uv run python showcase.py sequential
uv run python showcase.py loop
uv run python showcase.py cleanup
```

## Architecture

```
src/agent_vis/
├── __init__.py      # Public API exports
├── app.py           # FastAPI app, HTTP routes, WebSocket endpoint
├── config.py        # Pydantic settings (host, port, debug)
├── exceptions.py    # Custom exception hierarchy
├── models.py        # Pydantic models: Node, Edge, Flow, Workflow, WorkflowCreate, WorkflowUpdate
└── store.py         # WorkflowStore (in-memory), WebSocket broadcast logic, async flow removal
frontend/
├── index.html
├── app.js           # Canvas rendering, force-directed layout, WebSocket client
└── styles.css
tests/
├── conftest.py
├── test_api.py
└── test_e2e.py
showcase.py          # Demo scripts that hit the REST API and WebSocket
```

### Data flow

1. Clients create/update workflows via REST (`POST/PUT /workflows`).
2. On any mutation, `WorkflowStore._broadcast()` pushes JSON messages over all open WebSocket connections.
3. A new browser tab connects to `/ws`, receives an `init` message with all current workflows, then streams live `workflow_added/updated/deleted` and `flow_added/removed` events.
4. Flows have a `duration_ms` lifetime; `WorkflowStore._schedule_flow_removal()` uses `asyncio.create_task` to auto-remove them and broadcast `flow_removed`.
5. The frontend animates a particle along each flow's `path` (list of node IDs) using `requestAnimationFrame`.

### Key design details

- **In-memory only** — `WorkflowStore` is a module-level singleton (`store`) in `store.py`; all state is lost on server restart.
- **WebSocket `add_flow` message** — flows can also be injected directly via WebSocket (used by `showcase.py`), not just through REST. Note: the WebSocket handler in `app.py` bypasses `store.add_flow()` and manipulates `workflow.flows` directly.
- **Force-directed layout** — `app.js` runs a small physics simulation on `workflow_added` to position nodes; nodes are draggable by the user.
- **Node position keying** — positions are keyed as `wf_{workflowId}_{nodeId}` in the frontend `nodePositions` Map.
- **Test server** — `conftest.py` spins up a real uvicorn server in a daemon thread (`session` scope) and resets `store.workflows` between each test via `autouse` fixture; no mocking.

## Code Conventions

- Python 3.10+ type hints (`list[str]`, not `List[str]`); use `| None` for nullable.
- Pydantic v2 models for all data objects; call `.model_dump()` to serialize.
- Return types on all Python functions.
- Use `structlog` for structured logging.
- Use `pydantic-settings` for configuration management.
- JS: ES6+, `const`/`let`, camelCase for variables/functions, `UPPER_SNAKE_CASE` for constants.
- Add dependencies via `pyproject.toml`, then run `uv lock`.
