from __future__ import annotations

import io
import json
import os
import tempfile
from typing import Any, Dict, Iterator, Union


def ensure_workdir(path: str | None) -> str:
    """Return a usable working directory, creating a temp dir if None.

    Always creates the directory if it does not exist.
    """
    d = path or tempfile.mkdtemp(prefix="oai_batch_")
    os.makedirs(d, exist_ok=True)
    return d


def safe_write_text(path: str, data: str, *, encoding: str = "utf-8") -> str:
    """Atomically write text to `path` using a temp file + rename."""
    dir_name = os.path.dirname(path) or "."
    os.makedirs(dir_name, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", dir=dir_name)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(data)
        os.replace(tmp_path, path)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass
    return path


def safe_write_bytes(path: str, data: bytes) -> str:
    """Atomically write bytes to `path` using a temp file + rename."""
    dir_name = os.path.dirname(path) or "."
    os.makedirs(dir_name, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", dir=dir_name)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp_path, path)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass
    return path


def append_jsonl(path: str, obj_or_json: Union[str, Dict[str, Any]]) -> None:
    """Append a JSON or pre-serialized JSON string as a single JSONL line."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        if isinstance(obj_or_json, str):
            f.write(obj_or_json.rstrip() + "\n")
        else:
            f.write(json.dumps(obj_or_json, ensure_ascii=False) + "\n")


def iter_jsonl(path: str) -> Iterator[Dict[str, Any]]:
    """Iterate objects from a JSONL file (one JSON object per line)."""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def write_stream_like(content: Union[bytes, str, io.BufferedIOBase, io.RawIOBase, io.TextIOBase], dst_path: str) -> str:
    """Write an SDK `files.content(...)` response to disk.

    Supports either raw bytes/str or a stream-like object with `.read()`.
    """
    if hasattr(content, "read"):
        data = content.read()
    else:
        data = content
    if isinstance(data, (bytes, bytearray)):
        return safe_write_bytes(dst_path, bytes(data))
    else:
        return safe_write_text(dst_path, str(data))

