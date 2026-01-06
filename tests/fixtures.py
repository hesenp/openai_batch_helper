from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Obj:
    """Simple attribute-style object for mocks."""

    def __init__(self, **kw: Any) -> None:
        for k, v in kw.items():
            setattr(self, k, v)


class FakeFiles:
    def __init__(self) -> None:
        self.created: List[Dict[str, Any]] = []

    def create(self, *, file, purpose: str) -> Any:  # noqa: ANN001 - mimic SDK
        data = file.read()  # exhaust
        self.created.append({"purpose": purpose, "bytes": data})
        return Obj(id="file_123")

    def content(self, file_id: str) -> io.BytesIO:  # noqa: ARG002
        return io.BytesIO(b"{\"custom_id\":\"t1\",\"response\":{\"choices\":[{\"message\":{\"content\":\"ok\"}}]}}\n")


class FakeBatches:
    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}

    def create(self, *, input_file_id: str, endpoint: str, completion_window: str, metadata: Dict[str, str]):  # noqa: ANN001,E501
        b = Obj(id="batch_123", status="in_progress", input_file_id=input_file_id, endpoint=endpoint,
                completion_window=completion_window, metadata=metadata)
        self._store[b.id] = b
        return b

    def retrieve(self, batch_id: str):  # noqa: ANN001
        b = self._store[batch_id]
        # Simulate completing immediately on the next poll
        if b.status != "completed":
            b.status = "completed"
            b.output_file_id = "file_out_123"
        return b

    def cancel(self, batch_id: str):  # noqa: ANN001
        b = self._store.get(batch_id)
        if b:
            b.status = "canceled"
        return b


class FakeClient:
    def __init__(self) -> None:
        self.files = FakeFiles()
        self.batches = FakeBatches()

