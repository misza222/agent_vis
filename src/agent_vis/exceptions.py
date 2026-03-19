class AppError(Exception):
    """Base exception for application errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class WorkflowNotFoundError(AppError):
    """Raised when a workflow is not found."""

    def __init__(self, workflow_id: str) -> None:
        super().__init__(f"Workflow '{workflow_id}' not found")


class StoreError(AppError):
    """Raised when a store operation fails."""
