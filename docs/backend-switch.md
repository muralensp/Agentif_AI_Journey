# Backend Switch: Anthropic API SDK vs. Claude Agent SDK

This project can talk to Claude two different ways. One environment variable,
`LLM_BACKEND`, decides which one runs. This document explains what the two SDKs
are, how the switch is wired, how to configure each, and how to choose.

---

## 1. The two SDKs are different products

| | **Anthropic API SDK** | **Claude Agent SDK** |
|---|---|---|
| Package | `anthropic` | `claude-agent-sdk` |
| Import | `import anthropic` | `from claude_agent_sdk import query, ClaudeAgentOptions` |
| What it is | A thin client over `POST /v1/messages` | The Claude Code harness (agent loop, built-in tools, permissions, context mgmt) as a library |
| You write | The request; the loop, if any | A prompt + options |
| Tools | Only tools you define | Built-in `Read`/`Write`/`Edit`/`Bash`/`Glob`/`Grep`/`WebSearch`/`WebFetch` + MCP + subagents |
| Filesystem access | None | Yes (gated by `permission_mode` + `allowed_tools`) |
| Extra runtime dep | None | **Node.js 18+ on PATH** (drives the bundled Claude Code CLI) |
| Best for | Classification, summarization, extraction, Q&A, single calls | Open-ended tasks that need to read/modify files or take multiple tool-using steps |

Both authenticate with the same `ANTHROPIC_API_KEY`.

---

## 2. How the switch is wired

```
hello_world.py
  └─ config.load_config()        reads LLM_BACKEND + shared settings from env
  └─ backends.stream_reply()     dispatch: imports the chosen module lazily
       ├─ backends/api_backend.py     anthropic.AsyncAnthropic().messages.stream(...)
       └─ backends/agent_backend.py   claude_agent_sdk.query(prompt, ClaudeAgentOptions(...))
```

Both backends expose the **same function signature**:

```python
async def stream_reply(prompt: str, cfg: Config) -> AsyncIterator[str]: ...
```

so `hello_world.py` never needs to know which one it is calling. The dispatch in
`backends/__init__.py` imports the backend module **lazily**, so you only need
the dependencies for the backend you actually use (e.g. you can run the `api`
backend without Node.js installed).

---

## 3. Configuration

All settings are environment variables (see `.env.example`). A local `.env` is
auto-loaded when `python-dotenv` is installed.

| Variable | Used by | Default | Notes |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | both | — | required |
| `LLM_BACKEND` | switch | `api` | `api` or `agent` |
| `ANTHROPIC_MODEL` | both | `claude-haiku-4-5` | any current model id |
| `SYSTEM_PROMPT` | both | concise-assistant text | |
| `MAX_TOKENS` | `api` | `1024` | response cap for the single call |
| `AGENT_ALLOWED_TOOLS` | `agent` | `Read,Glob,Grep` | comma-separated; widen to allow writes/bash |
| `AGENT_MAX_TURNS` | `agent` | `3` | caps the agent loop |

### Switch to the API SDK

```powershell
$env:LLM_BACKEND = "api"
python hello_world.py "Summarize what this project does."
```

### Switch to the Agent SDK

```powershell
$env:LLM_BACKEND = "agent"
python hello_world.py "List the Python files here and describe hello_world.py."
```

Or set `LLM_BACKEND` once in `.env`.

---

## 4. Choosing a backend

Use the **API SDK** (`api`) when:

- The task is a single request/response (classify, summarize, extract, answer).
- You don't want a Node.js dependency.
- You want the lowest latency and cost.

Use the **Agent SDK** (`agent`) when:

- The task is open-ended and hard to fully specify up front.
- Claude needs to read or change files, run commands, or search the web.
- You want the built-in agent loop instead of writing your own.

If you find yourself hand-writing a `while stop_reason == "tool_use"` loop on top
of the API SDK, that is the signal to move to the Agent SDK (or to the API SDK's
`client.beta.messages.tool_runner` if you only need your own tools).

---

## 5. Extending

- **Give the agent write access:** set `AGENT_ALLOWED_TOOLS=Read,Write,Edit,Bash`
  and change `permission_mode` to `"acceptEdits"` in `backends/agent_backend.py`.
- **Multi-turn chat:** replace the single `messages.stream` call in
  `api_backend.py` with a running `messages` list; replace `query()` in
  `agent_backend.py` with `ClaudeSDKClient` for a persistent session.
- **A third backend** (e.g. Bedrock, or the API tool runner): add
  `backends/<name>_backend.py` with the same `stream_reply` signature and one
  `elif` in `backends/__init__.py`.
