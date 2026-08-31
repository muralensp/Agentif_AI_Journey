"""Runtime configuration and the backend switch.

One environment variable, ``LLM_BACKEND``, decides which implementation runs:

  * ``api``    -> backends/api_backend.py   (Anthropic API SDK - `anthropic`)
  * ``agent``  -> backends/agent_backend.py (Claude Agent SDK - `claude_agent_sdk`)

Everything else (model id, system prompt, max tokens, allowed tools) is shared
config so the two backends behave as similarly as possible. All values come from
environment variables, typically populated from a local ``.env`` (see
``.env.example``).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

# Load .env into os.environ before the dataclass field defaults are evaluated.
# NOTE: these three module-level names are used as the fallback values in Config
# below, so a .env (or real env vars) must define LLM_BACKEND, ANTHROPIC_MODEL,
# and MAX_TOKENS - otherwise they are None and Config construction fails.
try:  # python-dotenv is optional; real env vars work without it
    from dotenv import load_dotenv

    load_dotenv()

    LLM_BACKEND = os.getenv("LLM_BACKEND")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL")
    MAX_TOKENS = os.getenv("MAX_TOKENS")
except ModuleNotFoundError:
    pass

# The only accepted values for LLM_BACKEND; validated in Config.validate().
VALID_BACKENDS = ("api", "agent")


@dataclass
class Config:
    # field(default_factory=...) defers each lookup to instance-creation time so
    # tests can change the environment and get a fresh value.
    backend: str = field(default_factory=lambda: os.getenv("LLM_BACKEND", "api").lower())
    model: str = field(default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5"))
    system_prompt: str = field(
        default_factory=lambda: os.getenv(
            "SYSTEM_PROMPT",
            "You are a concise assistant. Answer in one or two sentences.",
        )
    )
    max_tokens: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS", 1024)))
    # Only used by the Agent SDK backend. Comma-separated tool names -> list;
    # defaults to a read-only set.
    allowed_tools: list[str] = field(
        default_factory=lambda: [
            t.strip()
            for t in os.getenv("AGENT_ALLOWED_TOOLS", "Read,Glob,Grep").split(",")
            if t.strip()
        ]
    )
    # Only used by the Agent SDK backend: hard cap on the agent loop.
    max_turns: int = field(default_factory=lambda: int(os.getenv("AGENT_MAX_TURNS", "3")))

    def validate(self) -> None:
        """Fail fast with a readable message on bad/missing config."""
        if self.backend not in VALID_BACKENDS:
            raise SystemExit(
                f"LLM_BACKEND={self.backend!r} is invalid. "
                f"Use one of: {', '.join(VALID_BACKENDS)}"
            )
        # Both backends authenticate with this key; check it here rather than
        # letting the SDK raise a less obvious error later.
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise SystemExit("ANTHROPIC_API_KEY is not set. See .env.example.")


def load_config() -> Config:
    """Build the Config from the environment and validate it. Use this, not Config()."""
    cfg = Config()
    cfg.validate()
    return cfg
