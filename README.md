# OpenAI Batch Helper

[![Tests](https://github.com/hesenp/openai_batch_helper/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/hesenp/openai_batch_helper/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/openai_batch_helper.svg)](https://pypi.org/project/openai_batch_helper/)
[![Docs](https://readthedocs.org/projects/openai-batch-helper/badge/?version=latest)](https://openai-batch-helper.readthedocs.io/en/latest/?badge=latest)

Running the OpenAI Batch API can cut per-request costs by roughly 50%. But the process through the default OpenAI Python SDK is very cumbersome. It requires users to  manage JSONL uploads, poll for status updates, download results in JSONL format again, and parse them. This quickly turns messy. The package `openai_batch_helper` helper keeps the batch flow tidy, typed, and production-friendly.

## Install

```
pip install openai-batch-helper
```

## Quickstart (add_task)

```python
from openai_batch_helper import BatchHelper, status_progress_logger

helper = BatchHelper(endpoint="/v1/chat/completions", completion_window="24h")
job = helper.init_job()

job.add_task(
    "t1",
    body={
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Be concise."},
            {"role": "user", "content": "Explain idempotency in one sentence."},
        ],
    },
)
job.add_task(
    "t2",
    body={
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Be concise."},
            {"role": "user", "content": "List 3 benefits of unit tests."},
        ],
    },
)

(job
 .submit_file()
 .submit_batch_job(metadata={"project": "demo"})
 .wait_for_completion(poll_seconds=5.0, on_update=status_progress_logger()))

print(job.download_result())
print(job.map_by_custom_id())
```

## Learn more

Check the docs for CLI usage, additional helpers, and troubleshooting: https://openai-batch-helper.readthedocs.io . 
