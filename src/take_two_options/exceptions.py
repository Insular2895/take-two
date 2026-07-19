"""Safety exceptions for deliberately unsupported operations."""


class ForbiddenOperation(RuntimeError):
    """Raised when a caller attempts an execution-side operation."""
