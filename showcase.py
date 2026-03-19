#!/usr/bin/env python3
"""
Sample script to showcase the workflow visualization tool.
Creates a sample workflow and sends flows through it.
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"


def create_workflow(workflow_id: str, name: str = None):
    """Create a sample workflow with nodes and edges."""
    nodes = [
        {"id": "start", "label": "Start"},
        {"id": "process1", "label": "Process 1"},
        {"id": "process2", "label": "Process 2"},
        {"id": "decision", "label": "Decision"},
        {"id": "action_a", "label": "Action A"},
        {"id": "action_b", "label": "Action B"},
        {"id": "end", "label": "End"},
    ]

    edges = [
        {"from_node": "start", "to_node": "process1"},
        {"from_node": "process1", "to_node": "process2"},
        {"from_node": "process2", "to_node": "decision"},
        {"from_node": "decision", "to_node": "action_a"},
        {"from_node": "decision", "to_node": "action_b"},
        {"from_node": "action_a", "to_node": "end"},
        {"from_node": "action_b", "to_node": "end"},
    ]

    data = {
        "id": workflow_id,
        "nodes": nodes,
        "edges": edges,
        "flows": [],
    }

    response = requests.post(f"{BASE_URL}/workflows", json=data)
    response.raise_for_status()
    print(f"Created workflow: {workflow_id}")
    return response.json()


def send_flow(workflow_id: str, path: list[str], duration_ms: int = 5000):
    """Send a flow through a path in the workflow."""
    flow = {
        "id": f"flow_{int(time.time() * 1000)}",
        "path": path,
        "duration_ms": duration_ms,
    }

    ws_url = BASE_URL.replace("http", "ws") + "/ws"
    import websocket

    ws = websocket.create_connection(ws_url)
    message = {
        "type": "add_flow",
        "workflow_id": workflow_id,
        "flow": flow,
    }
    ws.send(json.dumps(message))
    ws.close()
    print(f"Sent flow: {' -> '.join(path)}")


def demo_basic():
    """Basic demo: create workflow and send one flow."""
    print("\n=== Basic Demo ===\n")

    wf_id = "demo_basic"
    create_workflow(wf_id)

    print("\nSending flow through the path...")
    send_flow(
        wf_id, ["start", "process1", "process2", "decision", "action_a", "end"], 3000
    )
    print("Flow sent! Check the visualization.")


def demo_parallel():
    """Demo with parallel flows."""
    print("\n=== Parallel Flows Demo ===\n")

    wf_id = "demo_parallel"
    create_workflow(wf_id)

    print("\nSending multiple flows in parallel...")
    send_flow(
        wf_id, ["start", "process1", "process2", "decision", "action_a", "end"], 5000
    )
    send_flow(
        wf_id, ["start", "process1", "process2", "decision", "action_b", "end"], 5000
    )
    print("Flows sent! You should see two particles moving in parallel.")


def demo_sequential():
    """Demo with sequential flows."""
    print("\n=== Sequential Flows Demo ===\n")

    wf_id = "demo_sequential"
    create_workflow(wf_id)

    paths = [
        ["start", "process1", "process2", "decision", "action_a", "end"],
        ["start", "process1", "process2", "decision", "action_b", "end"],
    ]

    print("\nSending sequential flows...")
    for i, path in enumerate(paths):
        send_flow(wf_id, path, 4000)
        time.sleep(1)
    print("Sequential flows sent!")


def demo_loop():
    """Demo that continuously sends flows."""
    print("\n=== Continuous Flow Demo ===\n")

    wf_id = "demo_loop"
    create_workflow(wf_id)

    paths = [
        ["start", "process1", "process2", "decision", "action_a", "end"],
        ["start", "process1", "process2", "decision", "action_b", "end"],
    ]

    print("Sending continuous flows (Ctrl+C to stop)...")
    try:
        i = 0
        while True:
            path = paths[i % len(paths)]
            send_flow(wf_id, path, 8000)
            i += 1
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nStopped.")


def cleanup():
    """Delete all workflows."""
    response = requests.get(f"{BASE_URL}/workflows")
    workflows = response.json()
    for wf in workflows:
        requests.delete(f"{BASE_URL}/workflows/{wf['id']}")
    print("Cleaned up all workflows.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python showcase.py <demo>")
        print("  demo: basic, parallel, sequential, loop, cleanup")
        sys.exit(1)

    demo = sys.argv[1]

    try:
        import websocket  # noqa: F401
    except ImportError:
        print("Installing websockets library...")
        import subprocess

        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "websocket-client"]
        )

    if demo == "basic":
        demo_basic()
    elif demo == "parallel":
        demo_parallel()
    elif demo == "sequential":
        demo_sequential()
    elif demo == "loop":
        demo_loop()
    elif demo == "cleanup":
        cleanup()
    else:
        print(f"Unknown demo: {demo}")
