import httpx
from playwright.sync_api import Page, expect

BASE_TIMEOUT = 10_000  # ms


def navigate(page: Page, server_url: str) -> None:
    page.goto(server_url)
    expect(page.locator("#status")).to_have_text("Connected", timeout=BASE_TIMEOUT)


def test_page_loads_and_websocket_connects(page: Page, server_url: str):
    navigate(page, server_url)


def test_canvas_element_present(page: Page, server_url: str):
    navigate(page, server_url)
    expect(page.locator("#canvas")).to_be_visible()


def test_add_workflow_appears_in_list(page: Page, server_url: str):
    navigate(page, server_url)
    page.click("#addWorkflowBtn")
    expect(page.locator("#workflowList .workflow-item")).to_have_count(
        1, timeout=BASE_TIMEOUT
    )


def test_add_multiple_workflows(page: Page, server_url: str):
    navigate(page, server_url)
    page.click("#addWorkflowBtn")
    page.click("#addWorkflowBtn")
    expect(page.locator("#workflowList .workflow-item")).to_have_count(
        2, timeout=BASE_TIMEOUT
    )


def test_workflow_appears_in_select_dropdown(page: Page, server_url: str):
    navigate(page, server_url)
    page.click("#addWorkflowBtn")
    expect(
        page.locator("#workflowSelect option:not([value=''])"),
    ).to_have_count(1, timeout=BASE_TIMEOUT)


def test_delete_workflow_removes_from_list(page: Page, server_url: str):
    navigate(page, server_url)
    page.click("#addWorkflowBtn")
    expect(page.locator("#workflowList .workflow-item")).to_have_count(
        1, timeout=BASE_TIMEOUT
    )
    page.click(".delete-btn")
    expect(page.locator("#workflowList .workflow-item")).to_have_count(
        0, timeout=BASE_TIMEOUT
    )


def test_delete_workflow_removes_from_api(page: Page, server_url: str):
    navigate(page, server_url)
    page.click("#addWorkflowBtn")
    expect(page.locator("#workflowList .workflow-item")).to_have_count(
        1, timeout=BASE_TIMEOUT
    )
    page.click(".delete-btn")
    expect(page.locator("#workflowList .workflow-item")).to_have_count(
        0, timeout=BASE_TIMEOUT
    )
    assert httpx.get(f"{server_url}/workflows").json() == []


def test_add_flow_via_form(page: Page, server_url: str):
    navigate(page, server_url)
    page.click("#addWorkflowBtn")
    expect(page.locator("#workflowList .workflow-item")).to_have_count(
        1, timeout=BASE_TIMEOUT
    )
    page.select_option("#workflowSelect", index=1)  # index 0 is the placeholder
    page.fill("#flowPath", "n1,n2")
    page.fill("#flowDuration", "2000")
    page.click("#addFlowBtn")
    # Canvas animation cannot be inspected; verify no crash and workflow is still present
    expect(page.locator("#workflowList .workflow-item")).to_have_count(
        1, timeout=BASE_TIMEOUT
    )


def test_add_flow_with_empty_path_does_nothing(page: Page, server_url: str):
    navigate(page, server_url)
    page.click("#addWorkflowBtn")
    expect(page.locator("#workflowList .workflow-item")).to_have_count(
        1, timeout=BASE_TIMEOUT
    )
    page.select_option("#workflowSelect", index=1)
    # Leave #flowPath empty — JS guard prevents sending
    page.click("#addFlowBtn")
    expect(page.locator("#workflowList .workflow-item")).to_have_count(
        1, timeout=BASE_TIMEOUT
    )
