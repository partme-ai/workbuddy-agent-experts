"""Stable Harness error types."""


class HarnessError(RuntimeError):
    """An expected protocol or command failure with a stable code."""

    def __init__(self, code: str, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.retryable = retryable

