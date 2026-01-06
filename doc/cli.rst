Command-line interface
======================

Run a batch from an existing JSONL request file and print results path:

.. code-block:: bash

   python -m openai_batch_helper --input requests.jsonl \
     --endpoint /v1/chat/completions \
     --out results.jsonl \
     --poll-seconds 5 \
     --metadata project=demo env=dev \
     --progress -v

Flags
-----

- ``--input``: Path to the requests JSONL file.
- ``--endpoint``: Endpoint for the batch (e.g., ``/v1/chat/completions`` or ``/v1/embeddings``).
- ``--out``: Destination path for the downloaded results JSONL.
- ``--poll-seconds``: Polling interval for status checks.
- ``--completion-window``: Batch processing window (e.g., ``24h``).
- ``--metadata key=value``: Optional metadata pairs.
- ``--progress``: Enable progress logging to stderr.
- ``--heartbeat``: Heartbeat interval seconds (<=0 disables heartbeats).
- ``-v`` / ``-vv``: Increase verbosity.

Exit codes
----------

- ``0``: Success.
- ``1``: Failure during batch submission/download.
- ``2``: Input file not found.

