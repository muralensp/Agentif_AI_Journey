"""Claude Hello World - runs against either backend, chosen by LLM_BACKEND.

  LLM_BACKEND=api    python hello_world.py            # Anthropic API SDK
  LLM_BACKEND=agent  python hello_world.py            # Claude Agent SDK
  python hello_world.py "list the files in this folder"

This entrypoint is backend-agnostic: it only calls backends.stream_reply(), which
dispatches to the module the config selected. See docs/backend-switch.md for how
the switch works and when to use each.
"""

import sys

# anyio.run() drives the async code below without us writing asyncio boilerplate;
# it also works with either asyncio or trio.
import anyio

import backends
from config import load_config

# Human-readable description of what actually ran, keyed by cfg.backend.
BACKEND_INFO = {
    "api": "Anthropic API SDK (`anthropic`) - single stateless Messages API call, no tools",
    "agent": "Claude Agent SDK (`claude_agent_sdk`) - agentic loop with built-in tools",
}


async def run(prompt: str) -> None:
    # Reads LLM_BACKEND / ANTHROPIC_MODEL / etc. from the env and validates them
    # (exits with a message if the backend name or API key is missing).
    cfg = load_config()

    # Tell the user exactly which SDK / tier produced the reply below.
    print(f"Backend : {cfg.backend}  ->  {BACKEND_INFO.get(cfg.backend, 'unknown')}")
    print(f"Model   : {cfg.model}")
    print("-" * 72)

    # stream_reply is an async generator; print each chunk as it arrives so the
    # reply appears progressively instead of all at once.
    async for chunk in backends.stream_reply(prompt, cfg):
        print(chunk, end="", flush=True)
    print()  # final newline after the streamed text


def main() -> None:
    # Everything after "python hello_world.py" becomes the prompt; fall back to a
    # default so the script does something useful with no arguments.
    prompt = " ".join(sys.argv[1:]) or (
        "Say hello to the world and tell me one fun fact about agents."
    )
    anyio.run(run, prompt)


if __name__ == "__main__":
    main()
