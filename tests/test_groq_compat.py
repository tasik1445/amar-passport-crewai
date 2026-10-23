"""No CrewAI, network or API key needed for these regression tests."""
import sys
from types import SimpleNamespace

import pytest

from groq_compat import groq_cache_compatibility


def fake_litellm(monkeypatch):
    calls = []

    def completion(*args, **kwargs):
        calls.append((args, kwargs))
        return "OK"

    module = SimpleNamespace(completion=completion)
    monkeypatch.setitem(sys.modules, "litellm", module)
    return module, calls, completion


def test_removes_only_groq_top_level_cache_breakpoints(monkeypatch):
    litellm, calls, original = fake_litellm(monkeypatch)
    messages = [
        {"role": "system", "content": "Policy agent", "cache_breakpoint": True},
        {"role": "user", "content": "Profile", "cache_breakpoint": True},
    ]
    with groq_cache_compatibility():
        result = litellm.completion(model="groq/openai/gpt-oss-20b", messages=messages, temperature=0.1)
    assert result == "OK"
    assert all("cache_breakpoint" not in item for item in calls[0][1]["messages"])
    assert calls[0][1]["temperature"] == 0.1
    assert messages[0]["cache_breakpoint"] is True  # no mutation
    assert litellm.completion is original  # restored


def test_other_providers_not_modified(monkeypatch):
    litellm, calls, original = fake_litellm(monkeypatch)
    messages = [{"role": "system", "content": "x", "cache_breakpoint": True}]
    with groq_cache_compatibility():
        litellm.completion(model="anthropic/claude-sonnet-4", messages=messages)
    assert calls[0][1]["messages"] is messages
    assert litellm.completion is original


def test_restored_even_after_exception(monkeypatch):
    litellm, _, original = fake_litellm(monkeypatch)
    with pytest.raises(ValueError, match="forced"):
        with groq_cache_compatibility():
            raise ValueError("forced")
    assert litellm.completion is original


def test_groq_messages_without_marker_still_work(monkeypatch):
    litellm, calls, _ = fake_litellm(monkeypatch)
    messages = [{"role": "user", "content": "Hello"}]
    with groq_cache_compatibility():
        litellm.completion(model="groq/openai/gpt-oss-20b", messages=messages)
    assert calls[0][1]["messages"] == messages


def test_nonlist_messages_pass_through(monkeypatch):
    litellm, calls, _ = fake_litellm(monkeypatch)
    with groq_cache_compatibility():
        litellm.completion(model="groq/openai/gpt-oss-20b", messages=None)
    assert calls[0][1]["messages"] is None
