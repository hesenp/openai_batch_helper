from __future__ import annotations

import os
import json
import pytest

from openai_batch_helper.core import BatchHelper
from openai_batch_helper.exceptions import EmptyBatchError, BatchNotCompletedError
from .fixtures import FakeClient, Obj, FakeBatches


def test_write_jsonl_and_count(tmp_path):
    helper = BatchHelper(client=FakeClient(), workdir=str(tmp_path))
    job = helper.init_job()
    job.add_line({"x": 1}).add_lines([{"y": 2}, json.dumps({"z": 3})])
    assert os.path.exists(job.path)


def test_empty_batch_guard(tmp_path):
    helper = BatchHelper(client=FakeClient(), workdir=str(tmp_path))
    job = helper.init_job()
    with pytest.raises(EmptyBatchError):
        job.submit_file()


def test_submit_wait_and_download(tmp_path):
    helper = BatchHelper(client=FakeClient(), workdir=str(tmp_path))
    job = helper.init_job()
    job.add_line({"custom_id": "t1", "method": "POST", "url": "/v1/chat/completions", "body": {}})
    (job.submit_file()
        .submit_batch_job()
        .wait_for_completion(poll_seconds=0))

    assert job.status == "completed"
    out_path = job.download_result()
    assert os.path.exists(out_path)
    rows = list(job.iter_results(out_path))
    assert rows and rows[0]["custom_id"] == "t1"


def test_download_before_completion_raises(tmp_path):
    helper = BatchHelper(client=FakeClient(), workdir=str(tmp_path))
    job = helper.init_job()
    job.add_line({"custom_id": "t1", "method": "POST", "url": "/v1/chat/completions", "body": {}})
    job.submit_file().submit_batch_job()
    with pytest.raises(BatchNotCompletedError):
        job.download_result()


def test_map_by_custom_id_parsing(tmp_path):
    helper = BatchHelper(client=FakeClient(), workdir=str(tmp_path))
    job = helper.init_job()
    job.add_line({"custom_id": "t1", "method": "POST", "url": "/v1/chat/completions", "body": {}})
    (job.submit_file()
        .submit_batch_job()
        .wait_for_completion(poll_seconds=0))
    job.download_result()
    m = job.map_by_custom_id()
    assert m == {"t1": "ok"}


def test_add_task_default_url_and_flow(tmp_path):
    helper = BatchHelper(client=FakeClient(), workdir=str(tmp_path))
    job = helper.init_job()
    # url should default to helper.endpoint (chat completions)
    job.add_task("t1", body={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}]})
    (job.submit_file()
        .submit_batch_job()
        .wait_for_completion(poll_seconds=0))
    job.download_result()
    assert job.map_by_custom_id() == {"t1": "ok"}


def test_add_task_explicit_url_writes_jsonl(tmp_path):
    helper = BatchHelper(client=FakeClient(), workdir=str(tmp_path))
    job = helper.init_job()
    job.add_task("emb-1", "/v1/embeddings", body={"model": "text-embedding-3-small", "input": "x"})
    # Verify the JSONL line wrote the explicit URL
    import json as _json
    with open(job.path, "r", encoding="utf-8") as f:
        line = _json.loads(f.readline())
    assert line["url"] == "/v1/embeddings"
    assert line["custom_id"] == "emb-1"


def test_resume_job_polls_and_downloads(tmp_path):
    fc = FakeClient()

    class PollOnceBatches(FakeBatches):
        def __init__(self) -> None:
            super().__init__()
            self.calls = 0

        def retrieve(self, batch_id: str):  # type: ignore[override]
            self.calls += 1
            b = self._store[batch_id]
            if self.calls >= 2 and b.status != "completed":
                b.status = "completed"
                b.output_file_id = "file_out_123"
            return b

    fc.batches = PollOnceBatches()
    fc.batches._store["batch_abc"] = Obj(id="batch_abc", status="in_progress")

    helper = BatchHelper(client=fc, workdir=str(tmp_path))
    job = helper.resume_job("batch_abc")

    assert fc.files.created == []
    assert fc.batches.calls == 1
    assert job.status == "in_progress"
    assert not os.path.exists(job.path)

    job.wait_for_completion(poll_seconds=0)
    assert fc.batches.calls >= 2
    assert job.status == "completed"
    out_path = job.download_result()
    assert os.path.exists(out_path)
