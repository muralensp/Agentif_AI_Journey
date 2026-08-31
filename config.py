"""Runtime configuration and the backend switch.

One environment variable, ``LLM_BACKEND``, decides which implementation runs:

  * ``api``    -> backends/api_backend.py   (Anthropic API SDK - `anthropic`)
  * ``agent``  -> backends/agent_backend.py (Claude Agent SDK - `claude_agent_sdk`)

Everything else (model id, system prompt, max tokens, allowed tools) is shared
config so the two backends behave as similarly as possible.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

try:  # optional: load a local .env if python-dotenv is installed
    from dotenv import load_dotenv

    load_dotenv()

    LLM_BACKEND = os.getenv("LLM_BACKEND")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL")
    MAX_TOKENS = os.getenv("MAX_TOKENS")
except ModuleNotFoundError:
    pass

VALID_BACKENDS = ("api", "agent")


@dataclass
class Config:
    backend: str = field(default_factory=lambda: os.getenv("LLM_BACKEND", LLM_BACKEND).lower())
    model: str = field(default_factory=lambda: os.getenv("ANTHROPIC_MODEL", ANTHROPIC_MODEL))
    system_prompt: str = field(
        default_factory=lambda: os.getenv(
            "SYSTEM_PROMPT",
            "You are a concise assistant. Answer in one or two sentences.",
        )
    )
    max_tokens: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS", MAX_TOKENS)))
    # Only used by the Agent SDK backend. Comma-separated tool names.
    allowed_tools: list[str] = field(
        default_factory=lambda: [
            t.strip()
            for t in os.getenv("AGENT_ALLOWED_TOOLS", "Read,Glob,Grep").split(",")
            if t.strip()
        ]
    )
    max_turns: int = field(default_factory=lambda: int(os.getenv("AGENT_MAX_TURNS", "3")))

    def validate(self) -> None:
        if self.backend not in VALID_BACKENDS:
            raise SystemExit(
                f"LLM_BACKEND={self.backend!r} is invalid. "
                f"Use one of: {', '.join(VALID_BACKENDS)}"
            )
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise SystemExit("ANTHROPIC_API_KEY is not set. See .env.example.")


def load_config() -> Config:
    cfg = Config()
    cfg.validate()
    return cfg
