import asyncio
from datetime import datetime
from typing import Optional

import structlog
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from .models import Flow, Workflow, WorkflowCreate, WorkflowUpdate

logger = structlog.get_logger()


class WorkflowStore:
    """In-memory store for workflows with WebSocket notification support."""

    def __init__(self) -> None:
        self.workflows: dict[str, Workflow] = {}
        self.clients: set[WebSocket] = set()
        self.active_flows: dict[str, tuple[Workflow, Flow, datetime]] = {}

    def create_workflow(self, data: WorkflowCreate) -> Workflow:
        """Create a new workflow and broadcast to connected clients."""
        workflow = Workflow(
            id=data.id,
            nodes=data.nodes,
            edges=data.edges,
            flows=data.flows,
        )
        self.workflows[data.id] = workflow
        logger.info("workflow_created", workflow_id=data.id)

        for flow in workflow.flows:
            self._schedule_flow_removal(workflow.id, flow)

        self._broadcast(
            {
                "type": "workflow_added",
                "workflow": workflow.model_dump(),
            }
        )

        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Retrieve a workflow by its ID."""
        return self.workflows.get(workflow_id)

    def list_workflows(self) -> list[Workflow]:
        """List all workflows in the store."""
        return list(self.workflows.values())

    def update_workflow(
        self, workflow_id: str, data: WorkflowUpdate
    ) -> Optional[Workflow]:
        """Update an existing workflow and broadcast changes."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None

        if data.nodes is not None:
            workflow.nodes = data.nodes
        if data.edges is not None:
            workflow.edges = data.edges
        if data.flows is not None:
            workflow.flows = data.flows
            for flow in workflow.flows:
                self._schedule_flow_removal(workflow_id, flow)

        logger.info("workflow_updated", workflow_id=workflow_id)
        self._broadcast(
            {
                "type": "workflow_updated",
                "workflow": workflow.model_dump(),
            }
        )

        return workflow

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow and broadcast the deletion."""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            logger.info("workflow_deleted", workflow_id=workflow_id)
            self._broadcast(
                {
                    "type": "workflow_deleted",
                    "id": workflow_id,
                }
            )
            return True
        return False

    def _schedule_flow_removal(self, workflow_id: str, flow: Flow) -> None:
        """Schedule automatic removal of a flow after its duration."""
        asyncio.create_task(self._remove_flow_after(workflow_id, flow))

    async def _remove_flow_after(self, workflow_id: str, flow: Flow) -> None:
        """Remove a flow after its duration expires."""
        await asyncio.sleep(flow.duration_ms / 1000)

        flow_key = f"{workflow_id}:{flow.id}"
        if flow_key in self.active_flows:
            del self.active_flows[flow_key]

        logger.debug("flow_removed", workflow_id=workflow_id, flow_id=flow.id)
        self._broadcast(
            {
                "type": "flow_removed",
                "workflow_id": workflow_id,
                "flow_id": flow.id,
            }
        )

    async def connect_websocket(self, websocket: WebSocket) -> None:
        """Accept a WebSocket connection and send initial state."""
        await websocket.accept()
        self.clients.add(websocket)
        logger.debug("websocket_connected", client_id=id(websocket))

        await websocket.send_json(
            {
                "type": "init",
                "workflows": [w.model_dump() for w in self.workflows.values()],
            }
        )

    def disconnect_websocket(self, websocket: WebSocket) -> None:
        """Remove a WebSocket client from active connections."""
        self.clients.discard(websocket)
        logger.debug("websocket_disconnected", client_id=id(websocket))

    def _broadcast(self, message: dict[str, object]) -> None:
        """Send a message to all connected WebSocket clients."""
        for client in list(self.clients):
            try:
                task = asyncio.create_task(client.send_json(message))

                def handle_task(t: asyncio.Task[None]) -> None:
                    try:
                        t.result()
                    except WebSocketDisconnect:
                        pass  # Client disconnected, normal
                    except Exception as e:
                        logger.warning(
                            "broadcast_send_failed",
                            error=str(e),
                        )

                task.add_done_callback(handle_task)
            except Exception as e:
                logger.warning(
                    "broadcast_failed",
                    client_id=id(client),
                    error=str(e),
                )

    def add_flow(self, workflow_id: str, flow: Flow) -> bool:
        """Add a flow to an existing workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return False

        workflow.flows.append(flow)
        self._schedule_flow_removal(workflow_id, flow)
        logger.info("flow_added", workflow_id=workflow_id, flow_id=flow.id)
        self._broadcast(
            {
                "type": "flow_added",
                "workflow_id": workflow_id,
                "flow": flow.model_dump(),
            }
        )
        return True


store = WorkflowStore()
