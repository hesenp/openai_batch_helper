Overview
========

What is openai-batch-helper?
----------------------------

``openai-batch-helper`` is a tiny, production-friendly wrapper around the OpenAI Batch API. It takes care of the JSONL plumbing—building request files, uploading, polling, downloading, and parsing—so you can focus on the prompts, not the wiring.

Why batch, why this helper?
---------------------------

- Batching can reduce per-request costs by roughly 50%.
- JSONL chores (escaping, appending, uploads/downloads) are repetitive and easy to get wrong.
- The helper adds strong typing, readable errors, and chainable methods while staying dependency-light.

What you get
------------

- Fluent API via ``BatchHelper`` and ``BatchJob`` for building, submitting, and waiting on jobs.
- Safe JSONL writers/readers with UTF-8 defaults and empty-file guards.
- Polling until terminal statuses (``completed``, ``failed``, ``canceled``, ``expired``) with optional progress callbacks.
- Easy downloads for output and error files.
- Parsing helpers that iterate rows or map them by ``custom_id`` with sensible defaults for chat and embeddings.

How it works (high level)
-------------------------

1. Add tasks to a JSONL (chat or embeddings) keyed by your ``custom_id``.
2. Upload the JSONL to the Files API with purpose ``"batch"``.
3. Create the batch job with your input file id, endpoint, and completion window.
4. Poll until the batch finishes.
5. Download the output JSONL (and the errors file, if present).
6. Parse rows by ``custom_id`` into a Python dict for easy consumption.

Public API (library)
--------------------

- ``BatchHelper``: creates new jobs and holds defaults (endpoint, completion window).
- ``BatchJob``: builds JSONL input, submits files, creates the batch, waits, downloads, and parses outputs.
- ``status_progress_logger``: logging-based progress callback for ``wait_for_completion``.
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

