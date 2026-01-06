from __future__ import annotations

from openai import OpenAI
import logging
from openai_batch_helper import BatchHelper, status_progress_logger


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    client = OpenAI()
    helper = BatchHelper(client, endpoint="/v1/embeddings", completion_window="24h")
    job = helper.init_job()

    texts = ["alpha", "beta", "gamma"]
    for i, t in enumerate(texts, 1):
        job.add_line({
            "custom_id": f"emb-{i}",
            "method": "POST",
            "url": "/v1/embeddings",
            "body": {
                "model": "text-embedding-3-small",
                "input": t,
            },
        })

    (job
     .submit_file()
     .submit_batch_job(metadata={"project": "demo-emb"})
     .wait_for_completion(poll_seconds=5.0, on_update=status_progress_logger()))

    out_path = job.download_result()
    print("Results file:", out_path)
    print(job.map_by_custom_id())


if __name__ == "__main__":
    main()
