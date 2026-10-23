"""Scoped workaround for CrewAI LiteLLM -> Groq `cache_breakpoint` error.

CrewAI sometimes sends a nonstandard top-level `cache_breakpoint` message
attribute. Groq rejects that attribute. This wrapper removes that attribute
only from Groq messages, and only while a synchronous CrewAI crew runs.

The original messages are never mutated; the underlying LiteLLM function
is restored in a `finally` block. Do not use concurrently with other crews.
"""
from __future__ import annotations

from contextlib import contextmanager
from functools import wraps
from typing import Iterator


@contextmanager
def groq_cache_compatibility() -> Iterator[None]:
    import litellm

    original_completion = litellm.completion

    @wraps(original_completion)
    def completion_without_groq_marker(*args, **kwargs):
        model = kwargs.get("model", "")
        messages = kwargs.get("messages")
        if isinstance(model, str) and model.startswith("groq/") and isinstance(messages, list):
            cleaned_messages = [
                {key: value for key, value in message.items() if key != "cache_breakpoint"}
                if isinstance(message, dict) else message
                for message in messages
            ]
            kwargs = dict(kwargs)
            kwargs["messages"] = cleaned_messages
        return original_completion(*args, **kwargs)

    litellm.completion = completion_without_groq_marker
    try:
        yield
    finally:
        litellm.completion = original_completion
