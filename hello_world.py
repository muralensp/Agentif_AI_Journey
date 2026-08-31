"""Claude Hello World - runs against either backend, chosen by LLM_BACKEND.

  LLM_BACKEND=api    python hello_world.py            # Anthropic API SDK
  LLM_BACKEND=agent  python hello_world.py            # Claude Agent SDK
  python hello_world.py "list the files in this folder"

See docs/backend-switch.md for how the switch works and when to use each.
"""

import sys

import anyio

import backends
from config import load_config


async def run(prompt: str) -> None:
    cfg = load_config()
    print(f"[backend: {cfg.backend} | model: {cfg.model}]\n")

    async for chunk in backends.stream_reply(prompt, cfg):
        print(chunk, end="", flush=True)
    print()


def main() -> None:
    prompt = " ".join(sys.argv[1:]) or (
        "Say hello to the world and tell me one fun fact about agents."
    )
    anyio.run(run, prompt)


if __name__ == "__main__":
    main()
