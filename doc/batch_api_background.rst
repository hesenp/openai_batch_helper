Batch API Background
====================

The OpenAI Batch API processes many requests asynchronously for a discount
compared to synchronous calls. You upload a JSONL file of requests, create a
batch job, then download an output JSONL once it completes.

Request JSONL format
--------------------

One JSON object per line with the shape:

.. code-block:: json

   {"custom_id":"req-1","method":"POST","url":"/v1/chat/completions","body":{...}}

Key fields:

- ``custom_id``: Your identifier used to correlate inputs and outputs.
- ``method``: Typically ``"POST"``.
- ``url``: API endpoint (e.g., ``"/v1/chat/completions"`` or ``"/v1/embeddings"``).
- ``body``: The request body for that endpoint.

Lifecycle
---------

Batches typically advance through: ``validating → in_progress → finalizing → completed``.
Terminal statuses are: ``completed``, ``failed``, ``canceled``, ``expired``.

Outputs
-------

- When ``completed``, the batch has an ``output_file_id`` (and possibly an
  ``error_file_id`` if some lines failed).
- The output JSONL lines mirror your inputs and include your ``custom_id`` plus
  a ``response`` (or ``error``) payload.

Endpoint alignment
------------------

Ensure the ``endpoint`` you pass to ``batches.create`` matches the ``url``
field used in each input JSONL line. Mismatches will cause errors.

