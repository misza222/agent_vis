import httpx


def test_list_workflows_empty(server_url):
    resp = httpx.get(f"{server_url}/workflows")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_workflow(server_url):
    payload = {
        "id": "wf1",
        "nodes": [{"id": "n1", "label": "Start"}, {"id": "n2", "label": "End"}],
        "edges": [{"from_node": "n1", "to_node": "n2"}],
        "flows": [],
    }
    resp = httpx.post(f"{server_url}/workflows", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "wf1"
    assert len(data["nodes"]) == 2


def test_list_workflows_after_create(server_url):
    httpx.post(
        f"{server_url}/workflows",
        json={"id": "wf_list", "nodes": [], "edges": [], "flows": []},
    )
    resp = httpx.get(f"{server_url}/workflows")
    assert resp.status_code == 200
    assert any(w["id"] == "wf_list" for w in resp.json())


def test_get_workflow(server_url):
    httpx.post(
        f"{server_url}/workflows",
        json={"id": "wf_get", "nodes": [], "edges": [], "flows": []},
    )
    resp = httpx.get(f"{server_url}/workflows/wf_get")
    assert resp.status_code == 200
    assert resp.json()["id"] == "wf_get"


def test_get_nonexistent_workflow(server_url):
    assert httpx.get(f"{server_url}/workflows/nonexistent").status_code == 404


def test_delete_workflow(server_url):
    httpx.post(
        f"{server_url}/workflows",
        json={"id": "wf_del", "nodes": [], "edges": [], "flows": []},
    )
    resp = httpx.delete(f"{server_url}/workflows/wf_del")
    assert resp.status_code == 200
    assert resp.json() == {"status": "deleted"}
    assert httpx.get(f"{server_url}/workflows/wf_del").status_code == 404


def test_delete_nonexistent_workflow(server_url):
    assert httpx.delete(f"{server_url}/workflows/nope").status_code == 404
