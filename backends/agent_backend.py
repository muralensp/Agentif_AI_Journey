"""Claude Agent SDK backend - one agentic turn with built-in tools.

The Agent SDK ships the Claude Code harness (agent loop, Read/Glob/Grep/Bash/...,
permissions, context management) as a library. Use this tier when the task is
open-ended and may need file access or several tool calls. Selected when
LLM_BACKEND=agent. See docs/backend-switch.md.

Requires Node.js 18+ on PATH in addition to the Python package - the SDK drives
the bundled Claude Code CLI under the hood.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

# Imported at module top level, so this file only loads when LLM_BACKEND=agent
# (backends/__init__.py imports the chosen backend lazily). That keeps the
# claude_agent_sdk / Node.js dependency optional for api-only users.
from claude_agent_sdk import (
    AssistantMessage,   # a turn produced by the model
    ClaudeAgentOptions,  # per-run configuration
    TextBlock,          # a plain-text piece of an AssistantMessage
    query,              # runs one agent request and streams back messages
)

from config import Config


async def stream_reply(prompt: str, cfg: Config) -> AsyncIterator[str]:
    """Yield the assistant's text as the agent works through the task."""
    options = ClaudeAgentOptions(
        model=cfg.model,
        system_prompt=cfg.system_prompt,
        allowed_tools=cfg.allowed_tools,   # e.g. ["Read", "Glob", "Grep"] - read-only by default
        permission_mode="default",         # prompt before anything outside allowed_tools
        max_turns=cfg.max_turns,           # cap the agent loop so it can't run away
    )

    # query() streams a sequence of message objects: tool calls, tool results,
    # and assistant turns. We only forward the assistant's visible text.
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                # An AssistantMessage may also hold tool-use blocks; skip those.
                if isinstance(block, TextBlock):
                    yield block.text
