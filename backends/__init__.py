"""Backend implementations. Pick one via config.Config.backend."""

from __future__ import annotations

from collections.abc import AsyncIterator

from config import Config


async def stream_reply(prompt: str, cfg: Config) -> AsyncIterator[str]:
    """Dispatch to the configured backend and yield text chunks."""
    if cfg.backend == "api":
        from backends.api_backend import stream_reply as impl
    elif cfg.backend == "agent":
        from backends.agent_backend import stream_reply as impl
    else:  # config.validate() should have caught this already
        raise ValueError(f"Unknown backend: {cfg.backend}")

    async for chunk in impl(prompt, cfg):
        yield chunk
