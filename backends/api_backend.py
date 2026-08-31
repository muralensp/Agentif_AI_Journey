"""Anthropic API SDK backend - a single stateless Messages API call.

This is the right tier for classification / summarization / Q&A: one request,
one streamed response, no tool loop. See docs/backend-switch.md.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import anthropic

from config import Config


async def stream_reply(prompt: str, cfg: Config) -> AsyncIterator[str]:
    client = anthropic.AsyncAnthropic()  # reads ANTHROPIC_API_KEY from the env

    async with client.messages.stream(
        model=cfg.model,
        max_tokens=cfg.max_tokens,
        system=cfg.system_prompt,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        async for text in stream.text_stream:
            yield text
