from __future__ import annotations

import argparse
from openai_batch_helper.cli import build_parser


def test_cli_parse_metadata_and_defaults():
    p = build_parser()
    ns = p.parse_args(["--input", "req.jsonl", "--metadata", "a=1", "b=two"])
    assert isinstance(ns, argparse.Namespace)
    assert ns.input == "req.jsonl"
    assert ns.endpoint == "/v1/chat/completions"
    assert ns.metadata == ["a=1", "b=two"]

