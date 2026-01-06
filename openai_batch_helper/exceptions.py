from __future__ import annotations

class BatchHelperError(Exception):
    """Base exception for openai_batch_helper."""


class EmptyBatchError(BatchHelperError):
    """Raised when attempting to submit an empty JSONL file."""


class BatchNotCompletedError(BatchHelperError):
    """Raised when results are requested before the batch is completed."""

