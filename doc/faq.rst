FAQ
===

What does this project do in one sentence?
------------------------------------------

It removes boilerplate for running OpenAI Batch jobs in Python, from building
JSONL inputs to downloading and parsing outputs.

Does it stream responses?
-------------------------

No. The Batch API is asynchronous and writes results to an output JSONL file when
processing completes.

Which endpoints are supported?
------------------------------

The helper focuses on ``/v1/chat/completions`` and ``/v1/embeddings`` because
they are reliable in batch mode. Ensure your per-line ``url`` matches the batch
``endpoint`` you pass during creation.

How do I see progress while waiting?
------------------------------------

Use the logging-based progress callback:

.. code-block:: python

   import logging
   from batch_helper import status_progress_logger

   logging.basicConfig(level=logging.INFO)
   job.wait_for_completion(on_update=status_progress_logger(heartbeat_seconds=30))

What errors can be raised?
--------------------------

- ``EmptyBatchError``: You attempted to submit an empty JSONL file.
- ``BatchNotCompletedError``: You tried to download results before completion.

What Python versions are supported?
-----------------------------------

Python 3.9+.

Can I customize result parsing?
-------------------------------

Yes, pass an ``extractor`` to ``map_by_custom_id`` to return any value you want
for each output row.

