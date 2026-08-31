# Claude Hello World (Python) - API SDK + Agent SDK

A minimal project that greets the world through Claude, using **either** of two
SDKs, selected at runtime by one environment variable:

- `LLM_BACKEND=api` -> the **Anthropic API SDK** (`anthropic`) - one stateless call.
- `LLM_BACKEND=agent` -> the **Claude Agent SDK** (`claude-agent-sdk`) - one
  agentic turn with the built-in Claude Code tools.

Same entrypoint, same `stream_reply(prompt, cfg)` interface - `hello_world.py`
never knows which one ran. Full explanation of the switch and how to choose:
**[docs/backend-switch.md](docs/backend-switch.md)**.

## Layout

```
config.py                 env-driven config + the backend switch value
hello_world.py            entrypoint - backend-agnostic
backends/__init__.py      lazy dispatch to the chosen backend
backends/api_backend.py   anthropic.AsyncAnthropic().messages.stream(...)
backends/agent_backend.py claude_agent_sdk.query(...)
agent.py                  standalone extra: a hand-written tool-use loop on the API SDK
docs/backend-switch.md    supporting document
```

## Prerequisites

| Requirement | For | Notes |
|---|---|---|
| Python 3.10+ | both | |
| `ANTHROPIC_API_KEY` | both | see `.env.example` |
| Node.js 18+ on PATH | `agent` backend only | the Python SDK drives the bundled Claude Code CLI |

## Setup

```powershell
cd claude-agent-hello-world
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

copy .env.example .env   # then edit .env, or just set env vars in the shell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

## Run

```powershell
# Anthropic API SDK
$env:LLM_BACKEND = "api"
python hello_world.py

# Claude Agent SDK
$env:LLM_BACKEND = "agent"
python hello_world.py "list the python files here and summarize hello_world.py"
```

## See the difference

Ask the **same question** through each backend:

```powershell
$env:LLM_BACKEND = "api"
python hello_world.py "What does this project do and how does the backend switch work?"
#  -> a plausible answer written from the prompt alone; it read no files

$env:LLM_BACKEND = "agent"
python hello_world.py "List the Python files here and explain how the backend switch works."
#  -> cites real filenames and quotes config.py / backends/__init__.py
```

The API SDK call is one request/response. The Agent SDK call runs an agent loop
with read-only file tools (`Read,Glob,Grep`), so its answer is grounded in the
actual repo. That contrast is the point of the project: reach for an agent when
the task needs to *read the world*, not by default.

## Configuration

All via environment variables (see `.env.example` and the table in
[docs/backend-switch.md](docs/backend-switch.md)): `LLM_BACKEND`,
`ANTHROPIC_MODEL`, `SYSTEM_PROMPT`, `MAX_TOKENS`, `AGENT_ALLOWED_TOOLS`,
`AGENT_MAX_TURNS`.

> **Cost note:** `ANTHROPIC_MODEL` defaults to `claude-opus-5`. Set it to
> `claude-sonnet-5` or `claude-haiku-4-5` in `.env` for cheaper runs while
> experimenting.

## Extra: `agent.py`

A standalone script (not wired into the backend switch) that shows the tier
*between* a single call and the Agent SDK: a hand-written
`while stop_reason == "tool_use"` loop over a custom `lookup_order` tool.
Run it directly with `python agent.py "where is my order 4821?"`. If you find
yourself growing this loop, that's the signal to move to the Agent SDK or the
API SDK's `client.beta.messages.tool_runner`.
