Usage
=====

Minimal example
---------------

.. code-block:: python

   from batch_helper import BatchHelper

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

   (job
       .submit_file()
       .submit_batch_job(metadata={"project": "demo"})
       .wait_for_completion(poll_seconds=5))

   out_path = job.download_result()
   print("Results file:", out_path)
   print(job.map_by_custom_id())

Convenience: add_task
---------------------

Reduce boilerplate by letting the helper build the per-line JSON:

.. code-block:: python

   # url defaults to the helper's endpoint (here: /v1/chat/completions)
   job.add_task(
       "t1",
       body={
           "model": "gpt-4o-mini",
           "messages": [{"role": "user", "content": "Hello"}],
       },
   )

   # Explicit URL for embeddings
   job.add_task(
       "emb-1",
       "/v1/embeddings",
       body={"model": "text-embedding-3-small", "input": "alpha"},
   )

Embeddings example
------------------

.. code-block:: python

   from batch_helper import BatchHelper

   helper = BatchHelper(endpoint="/v1/embeddings", completion_window="24h")
   job = helper.init_job()

   for i, text in enumerate(["alpha", "beta", "gamma"], start=1):
       job.add_line({
           "custom_id": f"emb-{i}",
           "method": "POST",
           "url": "/v1/embeddings",
           "body": {"model": "text-embedding-3-small", "input": text},
       })

   (job.submit_file()
       .submit_batch_job()
       .wait_for_completion(poll_seconds=5))

   job.download_result()
   vectors = job.map_by_custom_id()  # dict of custom_id -> embedding vector

Progress logging
----------------

Use the built-in ``status_progress_logger`` for status transitions and periodic heartbeats:

.. code-block:: python

   import logging
   from batch_helper import status_progress_logger

   logging.basicConfig(level=logging.INFO)
   job.wait_for_completion(
       poll_seconds=5.0,
       on_update=status_progress_logger(heartbeat_seconds=30),
   )

Result parsing
--------------

``map_by_custom_id()`` extracts the most common payloads:

- Chat: ``response.choices[0].message.content``
- Embeddings: ``response.data[0].embedding``
- Otherwise, returns the raw ``response`` or ``{"error": ...}``

Custom extractors
-----------------

You can pass your own extractor function to ``map_by_custom_id``. The function
receives the full output row (a dict) and returns the value to store.

.. code-block:: python

   def only_model_name(row: dict) -> str | None:
       resp = row.get("response") or {}
       return resp.get("model")

   mapping = job.map_by_custom_id(extractor=only_model_name)

Errors file
-----------

If some inputs fail, the batch exposes ``error_file_id``. You can download it via
``job.download_errors()`` which returns the destination path or ``None`` if
there were no errors.

.. code-block:: python

   err_path = job.download_errors()
   if err_path:
       print("Errors written to:", err_path)
