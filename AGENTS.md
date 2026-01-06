# AGENTS.md

> Operator’s manual for AI coding agents (Codex/Copilot/ChatGPT) working on the **`batch-helper`** Python package.

This file tells you what the project is, what to change, and how to do it safely, reproducibly, and in the repo’s style.

---

## 1) Mission & Scope

Build and maintain a tiny, production-friendly Python helper around the OpenAI **Batch API** to hide boilerplate:

```python
from batch_helper import BatchHelper

helper = BatchHelper()
job = helper.init_job()
job.add_line({...}).add_lines([...]).submit_file().submit_batch_job().wait_for_completion()
path = job.download_result()
rows = job.map_by_custom_id()
```

Key goals:

* Minimal public API, strong typing, excellent docstrings.
* Zero heavy deps (only `openai`).
* Solid tests (unit + smoke).
* Clear CLI + examples.
* Helpful errors and guardrails (empty files, endpoint mismatch, etc).

Out of scope:

* Non-OpenAI batch providers.
* Async variants (for now).
* Distributed chunking / sharding (future).

---

## 2) Repository Map

```
batch-helper/
├─ batch_helper/
│  ├─ __init__.py
│  ├─ core.py           # BatchHelper, BatchJob, constants, exceptions
│  ├─ io.py             # JSONL writers/readers, streaming-safe file ops
│  ├─ cli.py            # `python -m batch_helper` entrypoint
│  ├─ typing.py         # Typed dicts / Protocols for request lines
│  └─ version.py
├─ examples/
│  ├─ chat_batch_minimal.py
│  └─ embeddings_batch_minimal.py
├─ tests/
│  ├─ test_core.py
│  ├─ test_io.py
│  └─ fixtures.py
├─ pyproject.toml
├─ README.md
├─ AGENTS.md            # (this file)
├─ CHANGELOG.md
└─ LICENSE
```

---

## 3) Public API (what to preserve)

### `batch_helper.core`

```python
from __future__ import annotations
from typing import Any, Dict, Iterable, Optional, Callable, Iterator, Union

TERMINAL_STATUSES = {"completed", "failed", "canceled", "expired"}

class BatchHelper:
    def __init__(
        self,
        client: "OpenAI | None" = None,
        *,
        endpoint: str = "/v1/chat/completions",
        completion_window: str = "24h",
        workdir: "str | None" = None,
    ): ...

    def init_job(self, *, filename: str | None = None) -> "BatchJob": ...

class BatchJob:
    # Building the JSONL
    def add_line(self, obj_or_json: Union[str, Dict[str, Any]]) -> "BatchJob": ...
    def add_lines(self, items: Iterable[Union[str, Dict[str, Any]]]) -> "BatchJob": ...

    # Submitting
    def submit_file(self) -> "BatchJob": ...
    def submit_batch_job(self, *, metadata: Optional[Dict[str, str]] = None) -> "BatchJob": ...

    # Lifecycle
    def wait_for_completion(self, *, poll_seconds: float = 5.0,
                            on_update: Optional[Callable[[Any], None]] = None) -> "BatchJob": ...
    def cancel(self) -> Any: ...

    # Results
    @property
    def status(self) -> Optional[str]: ...
    @property
    def batch_id(self) -> Optional[str]: ...
    @property
    def input_file_id(self) -> Optional[str]: ...
    @property
    def output_file_id(self) -> Optional[str]: ...
    @property
    def error_file_id(self) -> Optional[str]: ...

    def download_result(self, dst_path: str | None = None) -> str: ...
    def download_errors(self, dst_path: str | None = None) -> str | None: ...

    # Parsing helpers
    def iter_results(self, results_path: str | None = None) -> Iterator[Dict[str, Any]]: ...
    def map_by_custom_id(
        self,
        extractor: Optional[Callable[[Dict[str, Any]], Any]] = None,
        results_path: str | None = None,
    ) -> Dict[str, Any]: ...
```

### `batch_helper.io`

* Internal file utilities: safe writes, JSONL reader with backpressure, UTF-8 defaults.
* **Do not** expose I/O helpers in the top-level public API.

### CLI

* `python -m batch_helper --input requests.jsonl --endpoint /v1/chat/completions --out results.jsonl`
* Flags: `--poll-seconds`, `--metadata key=val`, `--completion-window 24h`
* Prints final status to stdout; non-zero exit on failure.

---

## 4) Style, Quality, and Constraints

* Python ≥ 3.9.
* Type hints everywhere; `mypy` clean (`strict = True` if practical).
* `ruff` (or `flake8`) clean.
* No dynamic monkey-patching.
* Keep public exceptions meaningful (e.g., `EmptyBatchError`, `BatchNotCompletedError`).

**Errors must explain:**

* Missing `submit_file()` call.
* Empty JSONL.
* Endpoint/URL mismatch suggestions.
* No `output_file_id` on completion.

---

## 5) How to Build/Run/Test

### Install (editable)

```bash
pip install -e .[dev]
```

Dev extras should include: `pytest`, `mypy`, `ruff`, `pytest-cov`, `types-requests`.

### Test

```bash
pytest -q
pytest -q --cov=batch_helper --cov-report=term-missing
mypy batch_helper
ruff check .
```

### Smoke example

```bash
python examples/chat_batch_minimal.py
```

*(Requires `OPENAI_API_KEY` in env; examples can be skipped in CI.)*

---

## 6) Implementation Notes (for agents)

1. **File handling**

   * Use `tempfile.mkdtemp()` when `workdir=None`.
   * Always open files with `encoding="utf-8"` for text / `rb` for uploads.
   * When downloading results via `client.files.content(file_id)`, support both stream-like objects (`.read()`) and raw bytes/str.

2. **Polling**

   * Poll statuses until in `TERMINAL_STATUSES`.
   * Store `output_file_id` and `error_file_id` when available.

3. **Parsing defaults**

   * `map_by_custom_id()` should:

     * Return chat content at `response.choices[0].message.content` if present.
     * Otherwise return `response` or `{"error": ...}`.

4. **Embeddings support**

   * If `response.data[0].embedding` exists, allow an optional extractor to return vectors.

5. **Zero-cost ergonomics**

   * Chainable methods.
   * Helpful `__repr__` / `__str__` with batch id + status.
   * Minimal logs; optional `on_update` callback during wait.

6. **Backwards compatibility**

   * Keep the method names and signatures stable.
   * If changing, add deprecation warnings and update README + examples.

---

## 7) Tasks the Agent Can Perform

* [ ] Implement `batch_helper/core.py` with the API above.
* [ ] Implement `batch_helper/io.py` with safe JSONL read/write utilities.
* [ ] Implement CLI (`batch_helper/cli.py`) using `argparse`.
* [ ] Add docstrings with short examples for each public method.
* [ ] Add unit tests:

  * [ ] Writing JSONL and counting lines.
  * [ ] Guarding empty batches.
  * [ ] Handling missing `output_file_id`.
  * [ ] Parsing happy-path chat results and error rows.
  * [ ] CLI argument wiring (parse only; no network in tests).
* [ ] Add example scripts for chat + embeddings.
* [ ] Wire `__all__` and `py.typed` if publishing types.
* [ ] Add `BatchNotCompletedError`, `EmptyBatchError`.

**Stretch (if time permits):**

* [ ] Progress reporter (`on_update`) that prints status transitions only.
* [ ] Endpoint sanity check: ensure each line’s `url` matches `BatchHelper.endpoint` (opt-in strict mode).
* [ ] `from_dataframe(df, builder=...)` convenience to build JSONL from tabular data.

---

## 8) Security & Secrets

* Never print API keys or full request bodies. Redact `Authorization` if logging.
* Do not write secrets to repo or example outputs.
* Examples should default to safe models and short prompts.

---

## 9) Release Process (for agents)

1. Bump version in `batch_helper/version.py` (SemVer).
2. Update `CHANGELOG.md` with highlights.
3. Ensure:

   * `pytest` passes with coverage ≥ 90% on `batch_helper/`.
   * `mypy` + `ruff` pass.
4. Build & check:

   ```bash
   python -m build
   twine check dist/*
   ```
5. (Maintainer step) Publish to PyPI.

---

## 10) Example: Minimal Usage in README

```python
from batch_helper import BatchHelper

helper = BatchHelper(endpoint="/v1/chat/completions", completion_window="24h")
job = helper.init_job()

job.add_lines([
    {
        "custom_id":"t1",
        "method":"POST",
        "url":"/v1/chat/completions",
        "body":{
            "model":"gpt-4o-mini",
            "messages":[
                {"role":"system","content":"Be concise."},
                {"role":"user","content":"Explain idempotency in one sentence."}
            ]
        }
    },
    {
        "custom_id":"t2",
        "method":"POST",
        "url":"/v1/chat/completions",
        "body":{
            "model":"gpt-4o-mini",
            "messages":[
                {"role":"user","content":"List 3 benefits of unit tests."}
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

---

## 11) Testing Strategy Details

* **Networkless unit tests**:

  * Mock `openai.OpenAI` client, `files.create`, `batches.create/retrieve`, and `files.content`.
  * Fixtures for:

    * Completed batch with `output_file_id`.
    * Failed batch with `error_file_id`.
    * Output JSONL lines for chat/embedding.

* **Parsing tests**:

  * Verify `iter_results()` yields dicts.
  * Verify `map_by_custom_id()` extracts expected content and handles errors.

* **CLI tests**:

  * `--input` nonexistent → nonzero exit.
  * Valid args with mocked client → success exit and calls.

---

## 12) Coding Conventions

* Prefer small, pure functions; keep `BatchJob` methods cohesive.
* Raise specific exceptions; avoid blanket `except Exception`.
* Keep dependencies minimal; **no** heavy frameworks.

---

## 13) Prompts You Can Use (for Codex)

* “Implement the `BatchJob.download_result` method with support for both stream-like and bytes responses.”
* “Create `batch_helper/cli.py` with argparse and a `main()` function, wiring flags to `BatchHelper` and `BatchJob`.”
* “Write unit tests in `tests/test_core.py` that mock the OpenAI client and cover the happy path and empty-batch error.”
* “Add docstrings with short code examples for `BatchHelper.init_job` and `BatchJob.map_by_custom_id`.”

---

## 14) Acceptance Criteria

A PR is “done” when:

* Public API matches section **3**.
* `pytest`, `mypy`, and `ruff` pass locally and in CI.
* Examples run with a real key and produce a `results.jsonl`.
* README shows a 15–20 line minimal example.
* Errors are human-friendly and actionable.

---

## 15) Future Roadmap (keep stubs small)

* Optional async variant (`await wait_for_completion()`).
* Auto-chunk large datasets and spawn multiple batches.
* Pluggable serializers (CSV/Parquet → JSONL).
* Rich progress (ETA from item counts).
