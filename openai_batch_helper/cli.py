from __future__ import annotations

import argparse
import sys
from typing import Dict
import logging

from .core import BatchHelper


def _parse_metadata(items: list[str]) -> Dict[str, str]:
    meta: Dict[str, str] = {}
    for it in items:
        if "=" in it:
            k, v = it.split("=", 1)
            meta[k] = v
    return meta


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="openai-batch-helper", description="OpenAI Batch helper CLI")
    p.add_argument("--input", required=True, help="Path to requests.jsonl")
    p.add_argument("--endpoint", default="/v1/chat/completions")
    p.add_argument("--out", default="results.jsonl", help="Path to write results.jsonl")
    p.add_argument("--poll-seconds", type=float, default=5.0)
    p.add_argument("--completion-window", default="24h")
    p.add_argument("--metadata", nargs="*", default=[], help="key=value pairs")
    p.add_argument("--progress", action="store_true", help="Log batch status progress to stderr")
    p.add_argument("--heartbeat", type=float, default=30.0, help="Seconds between progress heartbeats (use 0 or negative to disable)")
    p.add_argument("-v", "--verbose", action="count", default=0, help="Increase logging verbosity (-v or -vv)")
    return p


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    args = build_parser().parse_args(argv)

    # Configure logging if requested
    if args.progress or args.verbose:
        level = logging.WARNING
        if args.verbose == 1:
            level = logging.INFO
        elif args.verbose >= 2:
            level = logging.DEBUG
        logging.basicConfig(level=level, format="%(message)s")

    helper = BatchHelper(endpoint=args.endpoint, completion_window=args.__dict__["completion_window"])  # noqa: E501
    job = helper.init_job(filename=None)

    # Build: copy file lines as-is to job
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    job.add_line(line)
    except FileNotFoundError:
        print(f"Input file not found: {args.input}", file=sys.stderr)
        return 2

    try:
        on_update = None
        if args.progress:
            from .core import status_progress_logger

            hb = None if args.heartbeat is not None and args.heartbeat <= 0 else float(args.heartbeat)
            on_update = status_progress_logger(heartbeat_seconds=hb)

        (job
         .submit_file()
         .submit_batch_job(metadata=_parse_metadata(args.metadata))
         .wait_for_completion(poll_seconds=args.__dict__["poll_seconds"], on_update=on_update))
    except Exception as e:  # user-level tool, keep simple
        print(f"Batch failed to complete: {e}", file=sys.stderr)
        return 1

    try:
        out_path = job.download_result(args.out)
        print(job.status)
        print(out_path)
        return 0
    except Exception as e:
        print(f"Failed to download results: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
