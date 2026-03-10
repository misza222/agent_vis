import asyncio
import uuid
from typing import Optional
from datetime import datetime, timedelta
from fastapi import WebSocket
import json

from .models import Workflow, WorkflowCreate, WorkflowUpdate, Flow


class WorkflowStore:
    def __init__(self):
        self.workflows: dict[str, Workflow] = {}
        self.clients: set[WebSocket] = set()
        self.active_flows: dict[str, tuple[Workflow, Flow, datetime]] = {}

    def create_workflow(self, data: WorkflowCreate) -> Workflow:
        workflow = Workflow(
            id=data.id,
            nodes=data.nodes,
            edges=data.edges,
            flows=data.flows,
        )
        self.workflows[data.id] = workflow

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
        return self.workflows.get(workflow_id)

    def list_workflows(self) -> list[Workflow]:
        return list(self.workflows.values())

    def update_workflow(
        self, workflow_id: str, data: WorkflowUpdate
    ) -> Optional[Workflow]:
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

        self._broadcast(
            {
                "type": "workflow_updated",
                "workflow": workflow.model_dump(),
            }
        )

        return workflow

    def delete_workflow(self, workflow_id: str) -> bool:
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            self._broadcast(
                {
                    "type": "workflow_deleted",
                    "id": workflow_id,
                }
            )
            return True
        return False

    def _schedule_flow_removal(self, workflow_id: str, flow: Flow):
        task = asyncio.create_task(self._remove_flow_after(workflow_id, flow))

    async def _remove_flow_after(self, workflow_id: str, flow: Flow):
        await asyncio.sleep(flow.duration_ms / 1000)

        flow_key = f"{workflow_id}:{flow.id}"
        if flow_key in self.active_flows:
            del self.active_flows[flow_key]

        self._broadcast(
            {
                "type": "flow_removed",
                "workflow_id": workflow_id,
                "flow_id": flow.id,
            }
        )

    async def connect_websocket(self, websocket: WebSocket):
        await websocket.accept()
        self.clients.add(websocket)

        await websocket.send_json(
            {
                "type": "init",
                "workflows": [w.model_dump() for w in self.workflows.values()],
            }
        )

    def disconnect_websocket(self, websocket: WebSocket):
        self.clients.discard(websocket)

    def _broadcast(self, message: dict):
        for client in self.clients:
            try:
                asyncio.create_task(client.send_json(message))
            except Exception:
                pass


store = WorkflowStore()
