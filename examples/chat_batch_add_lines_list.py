from __future__ import annotations

import logging
from openai import OpenAI
from openai_batch_helper import BatchHelper, status_progress_logger


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    client = OpenAI()
    helper = BatchHelper(client, endpoint="/v1/chat/completions", completion_window="24h")
    job = helper.init_job()

    items = [
        {
            "custom_id": "t1",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Be concise."},
                    {"role": "user", "content": "Explain idempotency in one sentence."},
                ],
            },
        },
        {
            "custom_id": "t2",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Be concise."},
                    {"role": "user", "content": "List 3 benefits of unit tests."},
                ],
            },
        },
    ]

    job.add_lines(items)

    (job
     .submit_file()
     .submit_batch_job(metadata={"project": "demo"})
     .wait_for_completion(poll_seconds=5.0, on_update=status_progress_logger()))

    out_path = job.download_result()
    print("Results file:", out_path)
    print(job.map_by_custom_id())


if __name__ == "__main__":
    main()

