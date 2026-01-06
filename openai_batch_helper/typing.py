from __future__ import annotations

from typing import Any, Dict, List, TypedDict, Union


class ChatMessage(TypedDict, total=False):
    role: str
    content: str


class ChatBody(TypedDict, total=False):
    model: str
    messages: List[ChatMessage]


class EmbeddingsBody(TypedDict, total=False):
    model: str
    input: Union[str, List[str]]


class BatchRequestLine(TypedDict, total=False):
    custom_id: str
    method: str
    url: str
    body: Dict[str, Any]

