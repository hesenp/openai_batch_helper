Usage
=====

Quickstart (chat with ``add_task``)
-----------------------------------

.. code-block:: python

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

Add embeddings tasks
--------------------

Use ``add_task`` with an explicit URL when targeting embeddings:

.. code-block:: python

   job.add_task(
       "emb-1",
       "/v1/embeddings",
       body={"model": "text-embedding-3-small", "input": "alpha"},
   )

Progress logging
----------------

Use the built-in ``status_progress_logger`` for status transitions and periodic heartbeats:

.. code-block:: python

   import logging
   from openai_batch_helper import status_progress_logger

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
