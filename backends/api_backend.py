"""Anthropic API SDK backend - a single stateless Messages API call.

This is the right tier for classification / summarization / Q&A: one request,
one streamed response, no tool loop. Selected when LLM_BACKEND=api.
See docs/backend-switch.md.
"""

from __future__ import annotations

# AsyncIterator is the return type both backends share so hello_world.py can
# consume either one the same way (async for chunk in ...).
from collections.abc import AsyncIterator

import anthropic

from config import Config


async def stream_reply(prompt: str, cfg: Config) -> AsyncIterator[str]:
    """Yield the response text in chunks as the model produces it."""
    # No api_key argument: the SDK reads ANTHROPIC_API_KEY from the environment
    # (config.load_config() has already verified it is set).
    client = anthropic.AsyncAnthropic()

    # .stream() opens a Server-Sent-Events connection; the context manager keeps
    # it open until the response is complete, then closes it.
    async with client.messages.stream(
        model=cfg.model,
        max_tokens=cfg.max_tokens,        # hard cap on this single response
        system=cfg.system_prompt,
        messages=[{"role": "user", "content": prompt}],  # no history - one shot
    ) as stream:
        # text_stream yields only the text deltas (skips usage/ping/other events).
        async for text in stream.text_stream:
            yield text
