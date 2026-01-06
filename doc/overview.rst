Overview
========

What is openai-batch-helper?
----------------------------

``openai-batch-helper`` is a tiny, production-friendly Python wrapper around the
OpenAI Batch API. It removes boilerplate around building request JSONL files,
submitting a batch, polling for completion, downloading the output file, and
parsing results back to a convenient mapping keyed by your ``custom_id``.

Why use it?
-----------

- Minimal public API designed for clarity and type-safety.
- Focused feature set: batching chat and embeddings requests with helpful
  guardrails (empty file, missing output file, lifecycle handling).
- Zero heavy dependencies; relies only on the official ``openai`` SDK.
- Works as both a Python library and a small CLI.

Key features
------------

- Fluent, chainable API via ``BatchHelper`` and ``BatchJob``.
- Simple JSONL append/read helpers with UTF-8 defaults and safe writes.
- Polling until terminal statuses (``completed``, ``failed``, ``canceled``, ``expired``).
- Easy downloads for results and error files.
- Parsing helpers: iterate results or map them by ``custom_id`` with sensible
  defaults (chat content, embeddings vectors, or raw response/error).
- Progress reporting via logging (status transitions and periodic heartbeats).

How it works (high level)
------------------------

1. Build a requests JSONL where each line is a request input object with your
   ``custom_id``, HTTP method (``POST``), ``url`` (endpoint), and request body.
2. Upload the JSONL to the Files API with purpose ``"batch"``.
3. Create the batch job with your input file id, target endpoint, and completion window.
4. Poll until the batch reaches a terminal status.
5. Download the output JSONL and (optionally) the error JSONL.
6. Parse rows by ``custom_id`` into a Python dict for simple consumption.

Public API (library)
--------------------

- ``BatchHelper``: creates new jobs and holds defaults (endpoint, completion window).
- ``BatchJob``: builds the JSONL input, submits files, creates the batch,
  waits for completion, downloads results, and parses outputs.
- ``status_progress_logger``: a logging-based progress callback for
  ``wait_for_completion``.
- Exceptions: ``EmptyBatchError`` and ``BatchNotCompletedError``.

CLI overview
------------

The CLI mirrors the library flow for existing JSONL input files:

.. code-block:: bash

   python -m openai_batch_helper \
     --input requests.jsonl \
     --endpoint /v1/chat/completions \
     --out results.jsonl \
     --progress -v

Design principles
-----------------

- Minimal surface area: keep the public API small and stable.
- Strong typing: include type hints and ship ``py.typed``.
- Friendly errors: explain common missteps (e.g., empty file, missing calls).
- Composable: callbacks for progress reporting; logging over printing.
- Tests-first: unit tests mock the OpenAI client and avoid network calls.

Non-goals (for now)
-------------------

- Async variants and distributed chunking/sharding.
- Non-OpenAI batching providers.
- Streaming responses (Batch API returns files when complete).

