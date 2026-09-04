# Agentic AI Journey - Development Workflow

## Project Overview

**Agentic AI Journey** is an educational Python project demonstrating two distinct approaches to using Claude (Anthropic's AI model):

1. **API Backend** (`LLM_BACKEND=api`) - Direct, stateless API calls using the Anthropic SDK
2. **Agent Backend** (`LLM_BACKEND=agent`) - Agentic loops with tool integration using the Claude Agent SDK

The project uses a **single entrypoint** with a **runtime backend switch**, allowing developers to compare the same prompt executed through two different SDK tiers without code duplication.

---

## Repository Structure

```
muralensp/Agentif_AI_Journey/
├── hello_world.py              Entrypoint - backend-agnostic interface
├── config.py                   Environment config & backend selector
├── agent.py                    Optional: hand-written tool-use loop (customer support demo)
├── backends/                   Backend implementations
│   ├── __init__.py            Lazy dispatcher
│   ├── api_backend.py         Anthropic API SDK implementation
│   └── agent_backend.py       Claude Agent SDK implementation
├── docs/
│   └── backend-switch.md      Detailed explanation of backend selection
├── requirements.txt            Python dependencies
├── .env.example               Environment variable template
├── .gitignore                 Git exclusions
└── README.md                  Project overview
```

---

## Technology Stack

- **Language:** Python 3.10+
- **Primary Dependencies:**
  - `anthropic` ≥0.40.0 - Anthropic API SDK (for API backend)
  - `claude-agent-sdk` ≥0.1.0 - Claude Agent SDK (for Agent backend)
  - `anyio` ≥4.0.0 - Async runtime abstraction (asyncio or trio)
  - `python-dotenv` ≥1.0.0 - Environment variable loader
- **Runtime Requirements:**
  - Node.js 18+ on PATH (required for Agent SDK only)

---

## Execution Flow

### Startup Phase
1. **User runs:** `python hello_world.py "your prompt here"`
2. **hello_world.py → run(prompt):**
   - Calls `load_config()` from `config.py`
   - Reads `LLM_BACKEND` environment variable
   - Validates required keys (`ANTHROPIC_API_KEY`, model, tokens)
   - Exits with helpful error if config is invalid

### Backend Selection (config.py)
```
Environment Variables ──┬──> LLM_BACKEND=api    ──> backends/api_backend.py
                        │
                        └──> LLM_BACKEND=agent  ──> backends/agent_backend.py
```

**Config values shared across both backends:**
- `ANTHROPIC_MODEL` - Model identifier (default: `claude-haiku-4-5`)
- `SYSTEM_PROMPT` - Role definition (default: "You are a concise assistant...")
- `MAX_TOKENS` - Response length limit (default: 1024)

**Agent-backend–only config:**
- `AGENT_ALLOWED_TOOLS` - Comma-separated read-only tools (default: `Read,Glob,Grep`)
- `AGENT_MAX_TURNS` - Agent loop iteration cap (default: 3)

### API Backend Execution (LLM_BACKEND=api)
```
hello_world.py
    ↓
backends.stream_reply(prompt, cfg)
    ↓
backends/api_backend.py::stream_reply()
    ↓
anthropic.AsyncAnthropic().messages.stream(
    model, system, max_tokens, messages=[{"role": "user", "content": prompt}]
)
    ↓
Stream text chunks to stdout
    ↓
Return (one request/response cycle, no tools used)
```

**Characteristics:**
- Stateless single call
- No external tool integration
- Answer generated purely from the prompt text
- Fast, low-cost

### Agent Backend Execution (LLM_BACKEND=agent)
```
hello_world.py
    ↓
backends.stream_reply(prompt, cfg)
    ↓
backends/agent_backend.py::stream_reply()
    ↓
claude_agent_sdk.query(prompt, tools=[Read, Glob, Grep], ...)
    ↓
Agent Loop (runs on bundled Claude Code CLI via Node.js):
  1. Send prompt + available tools to Claude
  2. If response is final text → return it
  3. If Claude requests a tool (file read, glob pattern, grep):
     - Execute tool on local filesystem
     - Feed result back to Claude
     - Loop (up to AGENT_MAX_TURNS)
    ↓
Stream text chunks to stdout
    ↓
Return (multiple request/response cycles, grounded in real file access)
```

**Characteristics:**
- Stateful multi-turn conversation
- Read-only filesystem access (no write/delete tools)
- Answer grounded in actual files and project structure
- Slower but more accurate for file-based questions

---

## Key Decision Points

### When to Use Each Backend

| Scenario | API Backend | Agent Backend |
|----------|-------------|---------------|
| General knowledge Q&A | ✓ Preferred | ✗ Overkill |
| "Explain this codebase" | ✗ Hallucinates | ✓ Reads actual files |
| Quick cost-sensitive tasks | ✓ Fast + cheap | ✗ Multiple calls |
| File discovery / search | ✗ Blind | ✓ Built-in tools |
| Reasoning over code | ✗ Struggles | ✓ Ground truth available |

### Config Validation

`config.py::load_config()` enforces:
1. `LLM_BACKEND` is one of `("api", "agent")`
2. `ANTHROPIC_API_KEY` environment variable is set (both backends need it)
3. Model name is a valid string (no validation of Anthropic model catalog)
4. `MAX_TOKENS` is a positive integer

Exits immediately with a readable error if any validation fails.

---

## Workflow Scenarios

### Scenario 1: Develop & Test API Backend
```bash
# Setup
export ANTHROPIC_API_KEY="sk-ant-..."
export LLM_BACKEND="api"
export ANTHROPIC_MODEL="claude-haiku-4-5"

# Edit backends/api_backend.py

# Test
python hello_world.py "test prompt"

# Iterate
# (modify stream_reply(), re-run)
```

### Scenario 2: Switch Backends to Compare Outputs
```bash
# Run against API backend (no file access)
export LLM_BACKEND="api"
python hello_world.py "What does this project do?"
# → Answer based on prompt alone; may be generic

# Run against Agent backend (reads files)
export LLM_BACKEND="agent"
python hello_world.py "What does this project do?"
# → Answer based on README.md, config.py, backends/__init__.py, etc.
```

### Scenario 3: Extend Agent Tools
1. Modify `AGENT_ALLOWED_TOOLS` in `.env` (affects `config.py::Config.allowed_tools`)
2. Claude Agent SDK interprets available tools and uses them if relevant
3. Re-run with `LLM_BACKEND="agent"`

**Note:** The Agent SDK's available tools are built-in (Read, Glob, Grep); custom tools require modifications to the Agent SDK, not just config.

### Scenario 4: Hand-Written Tool Loop (Advanced)
The standalone `agent.py` script demonstrates a manual implementation:
- Defines custom `lookup_order(order_id)` tool
- Writes the request→tool→response loop by hand
- Stops when Claude returns plain text (no more tool_use blocks)
- Useful for teaching or for scenarios where the Agent SDK is overkill

```bash
python agent.py
# → "Where is my order 4821?" → tool call → "Your order 4821 is shipped..."
```

---

## Async Architecture

Both backends use **async/await** via the `anyio` library, which abstracts over asyncio/trio:

```python
# hello_world.py
import anyio

async def run(prompt: str) -> None:
    cfg = load_config()
    async for chunk in backends.stream_reply(prompt, cfg):
        print(chunk, end="", flush=True)

def main() -> None:
    anyio.run(run, prompt)
```

**Benefits:**
- Streaming responses are non-blocking
- Scales well if integrated into a server or queue worker
- Runtime (asyncio or trio) is chosen at import time by anyio

---

## Environment Variable Reference

| Variable | Required | Backend | Default | Notes |
|----------|----------|---------|---------|-------|
| `ANTHROPIC_API_KEY` | Yes | Both | — | Anthropic API key; exits if missing |
| `LLM_BACKEND` | Yes | Both | `api` | One of `api`, `agent` |
| `ANTHROPIC_MODEL` | No | Both | `claude-haiku-4-5` | Model identifier (e.g. `claude-opus-5`) |
| `SYSTEM_PROMPT` | No | Both | "You are a concise assistant..." | Role prompt sent to Claude |
| `MAX_TOKENS` | No | Both | `1024` | Output length limit |
| `AGENT_ALLOWED_TOOLS` | No | Agent | `Read,Glob,Grep` | Comma-separated; Agent SDK defines which exist |
| `AGENT_MAX_TURNS` | No | Agent | `3` | Max iterations of the agent loop |

All variables (except `ANTHROPIC_API_KEY`) can be loaded from `.env` via `python-dotenv`.

---

## Common Workflows & Commands

### Setup
```bash
# Clone & install
git clone https://github.com/muralensp/Agentif_AI_Journey.git
cd Agentif_AI_Journey
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\Activate.ps1` on Windows
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env: set ANTHROPIC_API_KEY
```

### Run API Backend
```bash
export LLM_BACKEND=api
python hello_world.py "What is an agent?"
```

### Run Agent Backend
```bash
export LLM_BACKEND=agent
python hello_world.py "List the Python files and explain how the backend switch works"
```

### Run Hand-Written Tool Loop
```bash
python agent.py
```

### Compare Backends on Same Prompt
```bash
export LLM_BACKEND=api
python hello_world.py "Explain the config system"

export LLM_BACKEND=agent
python hello_world.py "Explain the config system"
```

---

## Code Entry Points

| File | Role | Entry Point |
|------|------|-------------|
| `hello_world.py` | Entrypoint | `main()` → `anyio.run(run, prompt)` |
| `config.py` | Config & validation | `load_config()` |
| `backends/__init__.py` | Dispatcher | `stream_reply(prompt, cfg)` |
| `backends/api_backend.py` | API implementation | `stream_reply()` – uses `anthropic.AsyncAnthropic()` |
| `backends/agent_backend.py` | Agent implementation | `stream_reply()` – uses `claude_agent_sdk.query()` |
| `agent.py` | Optional demo | `run_agent(user_message)` → manual tool loop |

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ User: python hello_world.py "your prompt"                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │ hello_world │ Read argv[1:] → prompt
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  config.py  │ load_config() → validate env
                    └──────┬──────┘
                           │
                    ┌──────▼──────────────────────┐
                    │ LLM_BACKEND env var?        │
                    └──────┬──────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐       ┌────▼────┐    ┌──────▼────────┐
    │ backend │       │ backend │    │ INVALID       │
    │ = api   │       │ = agent │    │ → exit error  │
    └────┬────┘       └────┬────┘    └───────────────┘
         │                 │
    ┌────▼───────────────┐ │    ┌──────────────────┐
    │ api_backend.py     │ │    │ agent_backend.py │
    │ ─────────────────  │ │    │ ──────────────── │
    │ anthropic.Stream() │ │    │ agent_sdk.query()│
    │ → 1 call/response  │ │    │ → multi-turn     │
    └────┬───────────────┘ │    │   w/ tools       │
         │                 │    └─────────┬────────┘
         │                 │              │
         └─────────────────┴──────────────┘
                           │
                    ┌──────▼──────┐
                    │  Stream     │ Print chunks
                    │  text to    │ as they arrive
                    │  stdout     │
                    └──────┬──────┘
                           │
                  ┌────────▼────────┐
                  │ Exit (process   │
                  │ complete)       │
                  └─────────────────┘
```

---

## Extension Points

### Add a New Backend
1. Create `backends/my_backend.py`
2. Implement `async def stream_reply(prompt: str, cfg: Config) -> AsyncGenerator[str, None]`
3. Update `backends/__init__.py` to dispatch on `cfg.backend == "my_backend"`
4. Add `"my_backend"` to `VALID_BACKENDS` in `config.py`
5. Set `LLM_BACKEND=my_backend` in `.env`

### Extend agent.py
- Modify the `tools` list to add custom tool definitions
- Expand `execute_tool()` to handle the new tool names
- Increase `MAX_ITERATIONS` if needed for complex workflows

### Modify Config Defaults
- Edit `.env.example` for documentation
- Update `config.py::Config` field defaults (e.g., default model, system prompt)
- Env vars always override defaults

---

## Summary

The **Agentic AI Journey** workflow is centered on a single, configurable entrypoint that demonstrates:

1. **Config-driven backend selection** – one env var switches between two SDK tiers
2. **Async streaming** – progressive text output via anyio
3. **Tool-use patterns** – compare grounded (Agent) vs. prompt-only (API) responses
4. **Manual vs. SDK tool loops** – `agent.py` teaches the mid-tier approach

Use the **API backend** for fast, stateless calls; use the **Agent backend** to ground responses in real filesystem context. The shared config system keeps both backends in sync so you can isolate the SDK difference from the business logic.
