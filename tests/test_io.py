from __future__ import annotations

import os
from openai_batch_helper.io import append_jsonl, iter_jsonl, ensure_workdir


def test_append_and_iter_jsonl(tmp_path):
    p = os.path.join(tmp_path, "requests.jsonl")
    append_jsonl(p, {"a": 1})
    append_jsonl(p, "{\"b\":2}")
    rows = list(iter_jsonl(p))
    assert rows == [{"a": 1}, {"b": 2}]


def test_ensure_workdir(tmp_path):
    d = ensure_workdir(str(tmp_path))
    assert os.path.isdir(d)

