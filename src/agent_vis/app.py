from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
from typing import Any

import structlog
from starlette.websockets import WebSocketDisconnect

from .config import settings
from .models import Flow, WorkflowCreate, WorkflowUpdate
from .store import store

logger = structlog.get_logger()

app = FastAPI(title="Workflow Visualizer")

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
async def get_index() -> FileResponse:
    """Serve the main HTML page."""
    return FileResponse("frontend/index.html")


@app.post("/workflows", response_model=dict)
async def create_workflow(workflow: WorkflowCreate) -> dict[str, Any]:
    """Create a new workflow."""
    result = store.create_workflow(workflow)
    return result.model_dump()


@app.get("/workflows", response_model=list[dict[str, Any]])
async def list_workflows() -> list[dict[str, Any]]:
    """List all workflows."""
    return [w.model_dump() for w in store.list_workflows()]


@app.get("/workflows/{workflow_id}", response_model=dict[str, Any])
async def get_workflow(workflow_id: str) -> dict[str, Any]:
    """Get a specific workflow by ID."""
    workflow = store.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.model_dump()


@app.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str) -> dict[str, str]:
    """Delete a workflow by ID."""
    if not store.delete_workflow(workflow_id):
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"status": "deleted"}


@app.put("/workflows/{workflow_id}", response_model=dict[str, Any])
async def update_workflow(workflow_id: str, data: WorkflowUpdate) -> dict[str, Any]:
    """Update an existing workflow."""
    workflow = store.update_workflow(workflow_id, data)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.model_dump()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Handle WebSocket connections for real-time updates."""
    await store.connect_websocket(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "add_flow":
                workflow_id = message.get("workflow_id")
                flow_data = message.get("flow")

                workflow = store.get_workflow(workflow_id)
                if workflow:
                    flow = Flow(**flow_data)
                    workflow.flows.append(flow)
                    store._schedule_flow_removal(workflow_id, flow)
                    store._broadcast(
                        {
                            "type": "flow_added",
                            "workflow_id": workflow_id,
                            "flow": flow.model_dump(),
                        }
                    )
    except WebSocketDisconnect:
        pass  # Normal disconnect
    except Exception as e:
        logger.warning("websocket_error", error=str(e))
    finally:
        store.disconnect_websocket(websocket)


if __name__ == "__main__":
    import uvicorn

    logger.info("starting_server", host=settings.host, port=settings.port)
    uvicorn.run(app, host=settings.host, port=settings.port)
