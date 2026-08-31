"""Claude Agent SDK backend - one agentic turn with built-in tools.

The Agent SDK ships the Claude Code harness (agent loop, Read/Glob/Grep/Bash/...,
permissions) as a library. Use this tier when the task is open-ended and may
need file access or multiple tool calls. See docs/backend-switch.md.

Requires Node.js 18+ on PATH in addition to the Python package.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    TextBlock,
    query,
)

from config import Config


async def stream_reply(prompt: str, cfg: Config) -> AsyncIterator[str]:
    options = ClaudeAgentOptions(
        model=cfg.model,
        system_prompt=cfg.system_prompt,
        allowed_tools=cfg.allowed_tools,
        permission_mode="default",
        max_turns=cfg.max_turns,
    )

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    yield block.text
