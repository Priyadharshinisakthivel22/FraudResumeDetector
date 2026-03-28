"""
Background task entrypoints placeholder.

This module is where Celery/RQ jobs should be wired for:
- profile fetch retries
- deferred notifications
- heavy NLP processing
"""


def noop() -> str:
    return "worker-ready"
