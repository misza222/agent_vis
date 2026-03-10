from pydantic import BaseModel
from typing import Optional


class Node(BaseModel):
    id: str
    label: str


class Edge(BaseModel):
    from_node: str
    to_node: str


class Flow(BaseModel):
    id: str
    path: list[str]
    duration_ms: int = 5000


class Workflow(BaseModel):
    id: str
    nodes: list[Node]
    edges: list[Edge]
    flows: list[Flow] = []


class WorkflowCreate(BaseModel):
    id: str
    nodes: list[Node]
    edges: list[Edge]
    flows: list[Flow] = []


class WorkflowUpdate(BaseModel):
    nodes: Optional[list[Node]] = None
    edges: Optional[list[Edge]] = None
    flows: Optional[list[Flow]] = None
