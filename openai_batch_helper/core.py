from __future__ import annotations

import os
import time
from typing import Any, Callable, Dict, Iterable, Iterator, Optional, Union
import sys
import logging

from .exceptions import EmptyBatchError, BatchNotCompletedError
from .io import ensure_workdir, append_jsonl, iter_jsonl, write_stream_like

# Terminal lifecycle statuses for batch jobs
TERMINAL_STATUSES = {"completed", "failed", "canceled", "expired"}

# Module logger for internal notices
_log = logging.getLogger("openai_batch_helper.core")


def status_progress_printer(
    stream: Any | None = None,
    *,
    heartbeat_seconds: float | None = 30.0,
) -> Callable[[Any], None]:
    """Return an ``on_update`` callback that prints progress.

    Behavior:
    - Prints on status transitions immediately.
    - Additionally, prints a heartbeat line every ``heartbeat_seconds`` even if
      the status hasn't changed (set to ``None`` to disable heartbeat).

    Example:
        >>> job.wait_for_completion(on_update=status_progress_printer())
        >>> # or, more frequent updates
        >>> job.wait_for_completion(on_update=status_progress_printer(heartbeat_seconds=10))
    """

    start = time.time()
    last_status: list[Optional[str]] = [None]
    last_emit: list[float] = [start - 10.0]  # ensure first call emits

    def _emit(prefix: str, status: Optional[str]) -> None:
        elapsed = int(time.time() - start)
        target = stream or sys.stderr
        print(f"{prefix}; waited {elapsed}s. status: {status}", file=target, flush=True)
        last_emit[0] = time.time()

    def _cb(b: Any) -> None:
        s = getattr(b, "status", None)
        if s != last_status[0]:
            _emit("job submitted" if last_status[0] is None else "status change", s)
            last_status[0] = s
            return
        if heartbeat_seconds is not None and (time.time() - last_emit[0]) >= heartbeat_seconds:
            _emit("waiting", s)

    return _cb


def status_progress_logger(
    logger: Any | None = None,
    *,
    level: int = logging.INFO,
    heartbeat_seconds: float | None = 30.0,
) -> Callable[[Any], None]:
    """Return an ``on_update`` callback that logs progress via ``logging``.

    - Logs immediately on first update ("job submitted").
    - Logs on each status transition.
    - Emits heartbeat every ``heartbeat_seconds`` even if unchanged (``None`` to disable).

    Example:
        >>> import logging
        >>> logging.basicConfig(level=logging.INFO)
        >>> job.wait_for_completion(on_update=status_progress_logger())
    """

    lg = logger or logging.getLogger("openai_batch_helper.progress")
    start = time.time()
    last_status: list[Optional[str]] = [None]
    last_emit: list[float] = [start - 10.0]

    def _emit(prefix: str, status: Optional[str]) -> None:
        elapsed = int(time.time() - start)
        lg.log(level, "%s; waited %ss. status: %s", prefix, elapsed, status)
        last_emit[0] = time.time()

    def _cb(b: Any) -> None:
        s = getattr(b, "status", None)
        if s != last_status[0]:
            _emit("job submitted" if last_status[0] is None else "status change", s)
            last_status[0] = s
            return
        if heartbeat_seconds is not None and (time.time() - last_emit[0]) >= heartbeat_seconds:
            _emit("waiting", s)

    return _cb


class BatchHelper:
    """Helper to manage the OpenAI Batch API.

    Example:
        >>> from openai_batch_helper import BatchHelper
        >>> helper = BatchHelper(endpoint="/v1/chat/completions", completion_window="24h")
        >>> job = helper.init_job()
        >>> _ = job.add_line({
        ...     "custom_id": "t1",
        ...     "method": "POST",
        ...     "url": "/v1/chat/completions",
        ...     "body": {"model":"gpt-4o-mini","messages":[{"role":"user","content":"hi"}]},
        ... })
        >>> # Submit only when ready:
        >>> # job.submit_file().submit_batch_job().wait_for_completion()
    """

    def __init__(
        self,
        client: "Any | None" = None,
        *,
        endpoint: str = "/v1/chat/completions",
        completion_window: str = "24h",
        workdir: "str | None" = None,
    ) -> None:
        # Delay importing OpenAI to allow tests without the dependency installed
        if client is None:
            try:
                from openai import OpenAI

                client = OpenAI()
            except Exception:
                # If OpenAI is not installed, leave as None and raise lazily if used
                client = None
        self.client = client
        self.endpoint = endpoint
        self.completion_window = completion_window
        self.workdir = workdir

    def init_job(self, *, filename: str | None = None) -> "BatchJob":
        return BatchJob(
            client=self.client,
            endpoint=self.endpoint,
            completion_window=self.completion_window,
            workdir=self.workdir,
            filename=filename,
        )

    def resume_job(self, batch_id: str) -> "BatchJob":
        """Resume an existing batch without resubmitting files.

        Args:
            batch_id: The ID of the batch to resume.
        """
        if self.client is None:  # pragma: no cover - defensive
            raise RuntimeError(
                "OpenAI client not available; install 'openai' or pass a client."
            )
        b = self.client.batches.retrieve(batch_id)
        return BatchJob.from_existing(
            client=self.client,
            endpoint=self.endpoint,
            completion_window=self.completion_window,
            workdir=self.workdir,
            filename=None,
            batch_obj=b,
        )


class BatchJob:
    """Represents a single batch job lifecycle and artifacts.

    Methods are chainable to allow a fluent style.
    """

    def __init__(
        self,
        *,
        client: Any,
        endpoint: str,
        completion_window: str,
        workdir: str | None,
        filename: str | None,
        existing_batch_id: str | None = None,
    ) -> None:
        self.client = client
        self.endpoint = endpoint
        self.completion_window = completion_window
        self.dir = ensure_workdir(workdir)
        self.path = os.path.join(self.dir, filename or "requests.jsonl")
        if existing_batch_id is None:
            with open(self.path, "w", encoding="utf-8"):
                pass
        self._lines = 0
        self._input_file_id: str | None = None
        self._batch_id: str | None = existing_batch_id
        self._batch_obj: Any | None = None
        self._output_file_id: str | None = None
        self._error_file_id: str | None = None

    @classmethod
    def from_existing(
        cls,
        *,
        client: Any,
        endpoint: str,
        completion_window: str,
        workdir: str | None,
        filename: str | None,
        batch_obj: Any,
    ) -> "BatchJob":
        job = cls(
            client=client,
            endpoint=endpoint,
            completion_window=completion_window,
            workdir=workdir,
            filename=filename,
            existing_batch_id=getattr(batch_obj, "id", None),
        )
        job._batch_obj = batch_obj
        job._output_file_id = getattr(batch_obj, "output_file_id", None)
        job._error_file_id = getattr(batch_obj, "error_file_id", None)
        return job

    # Building the JSONL
    def add_line(self, obj_or_json: Union[str, Dict[str, Any]]) -> "BatchJob":
        """Append a single request line to the JSONL file.

        Args:
            obj_or_json: A Python dict to be JSON-encoded, or a pre-serialized JSON string.
        """
        append_jsonl(self.path, obj_or_json)
        self._lines += 1
        return self

    def add_lines(self, items: Iterable[Union[str, Dict[str, Any]]]) -> "BatchJob":
        for it in items:
            self.add_line(it)
        return self

    def add_task(
        self,
        custom_id: str,
        url: Optional[str] = None,
        *,
        body: Dict[str, Any],
        method: str = "POST",
    ) -> "BatchJob":
        """Append a single request line using convenience parameters.

        The ``url`` defaults to the job's ``endpoint``. ``body`` is keyword-only
        to keep argument order unambiguous.

        Example:
            >>> job.add_task("t1", body={
            ...     "model": "gpt-4o-mini",
            ...     "messages": [{"role": "user", "content": "hi"}],
            ... })
            >>> job.add_task("emb-1", "/v1/embeddings", body={
            ...     "model": "text-embedding-3-small",
            ...     "input": "hello",
            ... })
        """
        line: Dict[str, Any] = {
            "custom_id": custom_id,
            "method": method,
            "url": url or self.endpoint,
            "body": body,
        }
        return self.add_line(line)

    # Submitting
    def _require_client(self) -> Any:
        if self.client is None:
            raise RuntimeError("OpenAI client not available; install 'openai' or pass a client.")
        return self.client

    def submit_file(self) -> "BatchJob":
        if self._lines == 0:
            raise EmptyBatchError("No lines added; the requests JSONL file is empty.")
        client = self._require_client()
        file_obj = client.files.create(file=open(self.path, "rb"), purpose="batch")
        self._input_file_id = getattr(file_obj, "id", None)
        return self

    def submit_batch_job(self, *, metadata: Optional[Dict[str, str]] = None) -> "BatchJob":
        if not self._input_file_id:
            raise RuntimeError("Call submit_file() before submit_batch_job().")
        client = self._require_client()
        b = client.batches.create(
            input_file_id=self._input_file_id,
            endpoint=self.endpoint,
            completion_window=self.completion_window,
            metadata=metadata or {},
        )
        self._batch_id = getattr(b, "id", None)
        self._batch_obj = b
        return self

    # Lifecycle
    def wait_for_completion(
        self,
        *,
        poll_seconds: float = 5.0,
        on_update: Optional[Callable[[Any], None]] = None,
    ) -> "BatchJob":
        if not self._batch_id:
            raise RuntimeError("No batch to wait on; call submit_batch_job().")
        client = self._require_client()
        while True:
            b = client.batches.retrieve(self._batch_id)
            self._batch_obj = b
            if on_update:
                try:
                    on_update(b)
                except Exception:
                    # User callback errors shouldn't break polling,
                    # but we log them for visibility/security linting.
                    _log.exception("on_update callback raised an exception; continuing polling")
            if getattr(b, "status", None) in TERMINAL_STATUSES:
                self._output_file_id = getattr(b, "output_file_id", None)
                self._error_file_id = getattr(b, "error_file_id", None)
                break
            time.sleep(poll_seconds)
        return self

    def cancel(self) -> Any:
        if not self._batch_id:
            raise RuntimeError("No batch to cancel; call submit_batch_job() first.")
        client = self._require_client()
        return client.batches.cancel(self._batch_id)

    # Results
    @property
    def status(self) -> Optional[str]:
        return getattr(self._batch_obj, "status", None)

    @property
    def batch_id(self) -> Optional[str]:
        return self._batch_id

    @property
    def input_file_id(self) -> Optional[str]:
        return self._input_file_id

    @property
    def output_file_id(self) -> Optional[str]:
        return self._output_file_id

    @property
    def error_file_id(self) -> Optional[str]:
        return self._error_file_id

    def download_result(self, dst_path: str | None = None) -> str:
        if self.status != "completed":
            raise BatchNotCompletedError(f"Batch not completed; current status is '{self.status}'.")
        if not self._output_file_id:
            raise RuntimeError("No output_file_id present on the batch.")
        client = self._require_client()
        content = client.files.content(self._output_file_id)
        dst = dst_path or os.path.join(self.dir, "results.jsonl")
        return write_stream_like(content, dst)

    def download_errors(self, dst_path: str | None = None) -> str | None:
        if not self._error_file_id:
            return None
        client = self._require_client()
        content = client.files.content(self._error_file_id)
        dst = dst_path or os.path.join(self.dir, "errors.jsonl")
        return write_stream_like(content, dst)

    # Parsing helpers
    def iter_results(self, results_path: str | None = None) -> Iterator[Dict[str, Any]]:
        p = results_path or os.path.join(self.dir, "results.jsonl")
        yield from iter_jsonl(p)

    def map_by_custom_id(
        self,
        extractor: Optional[Callable[[Dict[str, Any]], Any]] = None,
        results_path: str | None = None,
    ) -> Dict[str, Any]:
        """Return a map of `custom_id -> extracted_value`.

        Default extractor:
          - If chat: return `response.choices[0].message.content` when present.
          - If embeddings: return `response.data[0].embedding` when present.
          - Otherwise: return `response` or `{ "error": ... }`.
        """

        def default_extract(obj: Dict[str, Any]) -> Any:
            if "response" in obj and obj["response"]:
                resp = obj["response"]
                # chat
                if isinstance(resp, dict) and resp.get("choices"):
                    try:
                        return resp["choices"][0].get("message", {}).get("content")
                    except Exception:
                        return resp
                # embeddings
                if isinstance(resp, dict) and resp.get("data"):
                    try:
                        return resp["data"][0]["embedding"]
                    except Exception:
                        return resp
                return resp
            return {"error": obj.get("error")}

        take = extractor or default_extract
        out: Dict[str, Any] = {}
        for row in self.iter_results(results_path):
            cid = row.get("custom_id") or f"row-{len(out)+1}"
            out[cid] = take(row)
        return out

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return f"BatchJob(batch_id={self._batch_id!r}, status={self.status!r})"
