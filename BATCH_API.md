# What the OpenAI Batch API does (in one breath)

You upload a **JSONL** file where each line is a request (e.g., a Response API call or an embedding). OpenAI processes those requests asynchronously, usually within **24 hours**, writes all outputs to an **output file**, and you download/parse that file. Batches are **cheaper (typically \~50% off vs sync)**, **don’t stream**, and have **separate rate limits** from your normal API calls. ([OpenAI Help Center][1])

---

# Step-by-step (Python)

## 0) Install & init the SDK

```bash
pip install --upgrade openai
```

```python
from openai import OpenAI
client = OpenAI()  # uses OPENAI_API_KEY from env
```

## 1) Prepare a JSONL “requests file”

Each **line** is a *request input object* like this (Response API):

```json
{"custom_id":"req-1","method":"POST","url":"/v1/responses","body":{"model":"gpt-4.1-mini","input":"Summarize https://example.com in one sentence."}}
```

or for embeddings:

```json
{"custom_id":"emb-1","method":"POST","url":"/v1/embeddings","body":{"model":"text-embedding-3-small","input":"hello world"}}
```

Key fields:

* `custom_id` — your own ID to match inputs↔outputs later (string).
* `method` — always `"POST"` for normal calls.
* `url` — the endpoint for the request (e.g., `"/v1/responses"` or `"/v1/embeddings"`).
* `body` — the usual JSON body for that endpoint.

(That shape is the canonical per-line “request input object.”) ([GitHub][2])

Here’s quick Python to build a JSONL from a list of prompts:

```python
import json

rows = []
prompts = [
    "Write a 1-sentence summary of the moon landing.",
    "List 3 benefits of unit tests.",
]
for i, p in enumerate(prompts, start=1):
    rows.append({
        "custom_id": f"task-{i}",
        "method": "POST",
        "url": "/v1/responses",
        "body": {
            "model": "gpt-4.1-mini",
            "input": f"Be concise. {p}",
        },
    })

with open("requests.jsonl", "w", encoding="utf-8") as f:
    for row in rows:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
```

## 2) Upload the JSONL to **Files** (purpose=`"batch"`)

```python
input_file = client.files.create(
    file=open("requests.jsonl", "rb"),
    purpose="batch",
)
```

## 3) Create the batch job

```python
batch = client.batches.create(
    input_file_id=input_file.id,
    endpoint="/v1/responses",        # must match the kind of requests in your JSONL
    completion_window="24h",          # current window
    metadata={"note": "demo batch"},
)
print(batch.id, batch.status)
```

> Notes
> • Batches are processed within a 24-hour window and don’t stream. ([OpenAI Help Center][1])
> • Make sure `endpoint` (here `"/v1/responses"`) matches the `url` field in each JSONL line. A mismatch will error. The Response API is the recommended surface for text generation going forward; switch to another endpoint (e.g., `"/v1/chat/completions"`) only if you need legacy compatibility. ([GitHub][3])

## 4) Poll for completion

```python
import time

def wait_for_batch(batch_id: str, poll=5):
    while True:
        b = client.batches.retrieve(batch_id)
        print("status:", b.status)
        if b.status in ("completed", "failed", "canceled", "expired"):
            return b
        time.sleep(poll)

batch = wait_for_batch(batch.id)
```

Batch statuses you’ll see: **validating → in\_progress → finalizing → completed** (or **failed / canceled / expired**). ([OpenAI Help Center][1])

## 5) Download the results file

When `status == "completed"`, you’ll have an `output_file_id` (and, if some lines failed, an `error_file_id`). Download the output:

```python
# Save the JSONL output locally
content = client.files.content(batch.output_file_id)
with open("results.jsonl", "wb") as f:
    f.write(content.read())  # .read() or .text depending on SDK version
```

## 6) Parse the outputs (map by `custom_id`)

Each line in the output JSONL corresponds to an input line and includes your `custom_id` plus the model’s response object (or an error). With the Response API the useful text lives under `response.output[*].content[*].text`:

```python
results = {}
with open("results.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        cid = obj["custom_id"]
        if "response" in obj and obj["response"]:
            resp = obj["response"]
            chunks = []
            for item in resp.get("output", []):
                for part in item.get("content", []):
                    if part.get("type") == "output_text":
                        chunks.append(part.get("text", ""))
            results[cid] = "".join(chunks) if chunks else resp
        else:
            results[cid] = {"error": obj.get("error")}
```

At this point you can join results back to your original rows via `custom_id`.

---

## Handy management calls

```python
# List recent batches
for b in client.batches.list(limit=10).data:
    print(b.id, b.status)

# Cancel a batch (if it's still running)
client.batches.cancel(batch.id)
```

---

## Common gotchas & tips

* **Pricing & discounts:** Batch processing is billed at a **discount vs synchronous usage (≈50%)**; check the pricing page for your exact model. ([OpenAI Help Center][1], [OpenAI][4])
* **No streaming:** Batch doesn’t support streaming; expect a file when all is done. ([OpenAI Help Center][1])
* **Rate limits:** Batch has **separate limits** from the synchronous APIs. ([OpenAI Help Center][1])
* **Status meanings & SLA:** Expect validation, in-progress, finalizing, completed; batches target completion **within 24 hours**. If a batch **expires**, partial results (completed lines) are returned. ([OpenAI Help Center][1])
* **Endpoint alignment:** Ensure the JSONL line `url` matches the `endpoint` you pass to `batches.create`. For text generation, point both at `"/v1/responses"`; switch to another endpoint only if the model you need isn’t exposed via Responses. ([GitHub][3])
* **Images & other models:** Batch supports images and most models, but not all—check your chosen model’s reference page first. ([OpenAI Help Center][1])
* **Helper extractor:** `BatchJob.map_by_custom_id()` hands back the raw `response` payload for Response API rows; pass a custom `extractor` (see below) if you want plain text.

---

## How this repo’s helper maps to the raw API steps

Everything above is the manual OpenAI workflow. The `batch_helper` package in this
repository wraps those steps so you can focus on the JSONL lines and let the helper
handle file uploads, batch creation, polling, and downloads.

```python
from batch_helper import BatchHelper, status_progress_logger

helper = BatchHelper(endpoint="/v1/responses", completion_window="24h")
job = helper.init_job()

prompts = ["Explain idempotency in one sentence.", "List 3 benefits of unit tests."]
for i, prompt in enumerate(prompts, 1):
    job.add_task(
        custom_id=f"task-{i}",
        body={
            "model": "gpt-4.1-mini",
            "input": f"Be concise. {prompt}",
        },
    )

(job
 .submit_file()
 .submit_batch_job(metadata={"project": "demo"})
 .wait_for_completion(poll_seconds=5, on_update=status_progress_logger()))

out_path = job.download_result()


def to_text(row: dict) -> str:
    resp = row.get("response", {})
    chunks: list[str] = []
    for item in resp.get("output", []):
        for part in item.get("content", []):
            if part.get("type") == "output_text":
                chunks.append(part.get("text", ""))
    return "".join(chunks) if chunks else str(resp)


print(job.map_by_custom_id(extractor=to_text))

# Resume an existing job if you already have the batch ID
job = helper.resume_job("batch_abc")
job.wait_for_completion(on_update=status_progress_logger())
```

### CLI quick start

The package also exposes a CLI that translates directly to the six core steps:

```
python -m batch_helper --input requests.jsonl --endpoint /v1/responses \
  --out results.jsonl --poll-seconds 5 --metadata project=demo env=dev \
  --completion-window 24h --progress
```

`--progress` enables heartbeat logging driven by `status_progress_logger`; disable
heartbeats with `--heartbeat 0` if you only want status transitions.


[1]: https://help.openai.com/en/articles/9197833-batch-api-faq "Batch API  FAQ | OpenAI Help Center"
[2]: https://github.com/openai/openai-python/issues/1937?utm_source=chatgpt.com "Missing type for batch request input and output objects · ..."
[3]: https://github.com/openai/openai-python/issues/2497 "Batch Endpoint and Request Input Object URL mismatch · Issue #2497 · openai/openai-python · GitHub"
[4]: https://platform.openai.com/docs/models/gpt-4o?snapshot=gpt-4o-2024-11-20&utm_source=chatgpt.com "Model - OpenAI API"
