from pydantic import BaseModel


class Node(BaseModel):
    """Represents a node in a workflow."""

    id: str
    label: str


class Edge(BaseModel):
    """Represents an edge between two nodes in a workflow."""

    from_node: str
    to_node: str


class Flow(BaseModel):
    """Represents a flow (animated particle) traveling through a workflow."""

    id: str
    path: list[str]
    duration_ms: int = 5000


class Workflow(BaseModel):
    """Represents a complete workflow with nodes, edges, and flows."""

    id: str
    nodes: list[Node]
    edges: list[Edge]
    flows: list[Flow] = []


class WorkflowCreate(BaseModel):
    """Request model for creating a new workflow."""

    id: str
    nodes: list[Node]
    edges: list[Edge]
    flows: list[Flow] = []


class WorkflowUpdate(BaseModel):
    """Request model for updating an existing workflow."""

    nodes: list[Node] | None = None
    edges: list[Edge] | None = None
    flows: list[Flow] | None = None
