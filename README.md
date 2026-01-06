# OpenAI Batch Helper

[![Tests](https://github.com/hesenp/openai_batch_helper/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/hesenp/openai_batch_helper/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/openai-batch-helper.svg)](https://pypi.org/project/openai-batch-helper/)
[![Docs](https://readthedocs.org/projects/openai-batch-helper/badge/?version=latest)](https://openai-batch-helper.readthedocs.io/en/latest/?badge=latest)

Tiny, production-friendly helper for the OpenAI Batch API.

## Installation

```
pip install openai-batch-helper
```

## Minimal Example

```python
from openai_batch_helper import BatchHelper

helper = BatchHelper(endpoint="/v1/chat/completions", completion_window="24h")
job = helper.init_job()

job.add_lines([
    {
        "custom_id": "t1",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Be concise."},
                {"role": "user", "content": "Explain idempotency in one sentence."}
            ]
        }
    }
])

(job.submit_file()
    .submit_batch_job(metadata={"project":"demo"})
    .wait_for_completion(poll_seconds=5))

out_path = job.download_result()
print("Results file:", out_path)
print(job.map_by_custom_id())
```

Resume an existing batch job and continue polling:

```python
job = helper.resume_job("batch_123")
job.wait_for_completion()
job.download_result()
```

## CLI

```
python -m openai_batch_helper --input requests.jsonl --endpoint /v1/chat/completions --out results.jsonl \
  --poll-seconds 5 --metadata project=demo env=dev --completion-window 24h
```

The package also installs a console script so you can run `openai-batch-helper` with the same flags, or `python -m openai_batch_helper ...`.

## Documentation

- Latest docs: https://openai-batch-helper.readthedocs.io
- Build locally:

```
pip install -e .[docs]
sphinx-build -b html doc/ doc/_build/html
```

## Development

```
pip install -e .[dev]
pytest -q
mypy openai_batch_helper
ruff check .
```

To cut a PyPI release:

```
python -m build
twine check dist/*
# then twine upload dist/*
```

Refer to `AGENTS.md` and `BATCH_API.md` for design and API background.

## CI/CD hooks

- Tests: GitHub Actions runs lint + unit tests on pushes/PRs (`.github/workflows/tests.yml`).
- Releases: Publishing is automated from GitHub releases via `.github/workflows/release.yml`; set `PYPI_API_TOKEN` secret in the repo to upload to PyPI.
- Docs: `.github/workflows/docs.yml` builds docs locally and triggers Read the Docs; set `RTD_TOKEN` secret and ensure the RTD project slug is `openai-batch-helper`.

## Examples

- `examples/chat_batch_minimal.py` — Chat batch using `add_line` in a loop.
  - Run: `python examples/chat_batch_minimal.py`
- `examples/embeddings_batch_minimal.py` — Embeddings batch using `add_line` in a loop.
  - Run: `python examples/embeddings_batch_minimal.py`
- `examples/chat_batch_add_task.py` — Chat batch using `add_task` convenience.
  - Run: `python examples/chat_batch_add_task.py`
- `examples/embeddings_batch_add_task.py` — Embeddings batch using `add_task`.
  - Run: `python examples/embeddings_batch_add_task.py`
- `examples/chat_batch_add_lines_list.py` — Chat batch using `add_lines([...])`.
  - Run: `python examples/chat_batch_add_lines_list.py`

All examples require `OPENAI_API_KEY` in your environment.
