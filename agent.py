"""Manual tool-use loop on the Anthropic API SDK (customer-support demo).

This is the tier *between* a single Messages API call (hello_world.py with
LLM_BACKEND=api) and the full Claude Agent SDK: we define one tool, and we
hand-write the request -> run tool -> feed result back loop ourselves.

Flow each turn:
  1. Send the conversation to Claude with the tool list.
  2. If Claude replied with plain text (stop_reason != "tool_use"), we're done.
  3. If Claude asked for a tool (stop_reason == "tool_use"), run it, append the
     result as a "tool_result" block, and loop again so Claude can use it.

Run:  python agent.py
"""

import os
import json

import anthropic
from dotenv import load_dotenv

# Loads a .env from this folder or any parent dir (finds ../.env at the
# ClaudeArchitecture root). Populates os.environ; existing env vars win.
load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key)

# Model id comes from .env (ANTHROPIC_MODEL), e.g. "claude-opus-5".
MODEL = os.getenv("ANTHROPIC_MODEL")

# Sent on every request as the "system" prompt: sets the assistant's role and,
# importantly, tells it to prefer the tool over guessing.
SYSTEM_PROMPT = (
    "You are a friendly customer-support agent for an online store. "
    "When a customer asks about an order, use the lookup_order tool to get "
    "real information before answering. Keep replies short and helpful."
)

# Tool schema advertised to Claude. Claude never runs code - it only emits a
# "tool_use" block with an "input" matching this schema; execute_tool() runs it.
tools = [
    {
        "name": "lookup_order",
        "description": (
            "Look up an order by its order id. "
            "Returns current status, estimated delivery date, and carrier name. "
            "Use this when the customer asks where their order is or when it will arrive."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The numeric order id (e.g. '4821')",
                }
            },
            "required": ["order_id"],
        },
    }
]


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Dispatch a tool call and return its result as a JSON string.

    The return value becomes the "content" of the tool_result block we send
    back to Claude, so it must be a string.
    """
    if tool_name == "lookup_order":
        order_id = tool_input.get("order_id", "")

        # Stand-in for a real database / orders API.
        mock_orders = {
            "4821": {"status": "shipped", "eta": "March 30", "carrier": "FedEx"},
            "9918": {"status": "processing", "eta": "April 2", "carrier": "UPS"},
            "0042": {"status": "delivered", "eta": "March 25", "carrier": "DHL"},
        }

        if order_id in mock_orders:
            return json.dumps(mock_orders[order_id])
        # Return a structured error rather than raising - Claude can read this
        # and tell the customer the order wasn't found.
        return json.dumps({"error": f"Order {order_id} not found"})

    return json.dumps({"error": f"Unknown tool: {tool_name}"})


def run_agent(user_message: str) -> str:
    """Run the tool-use loop until Claude produces a final answer.

    Returns the final text response.
    """

    # The API is stateless: we resend the whole conversation every turn.
    messages = [
        {"role": "user", "content": user_message}
    ]

    # Safety cap so a misbehaving model can't loop forever.
    MAX_ITERATIONS = 50
    iteration = 0

    while iteration < MAX_ITERATIONS:
        iteration += 1

        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

        # Record Claude's turn verbatim (text and/or tool_use blocks). Claude
        # must see its own tool_use block on the next request for the paired
        # tool_result to be valid.
        messages.append({"role": "assistant", "content": response.content})

        # stop_reason == "tool_use" means Claude wants a tool; anything else
        # ("end_turn", "max_tokens", ...) means it's finished talking.
        if response.stop_reason != "tool_use":
            # Concatenate the text blocks into the final answer.
            return "".join(
                block.text for block in response.content if block.type == "text"
            )

        # Claude asked for one or more tools. Run them all and return every
        # tool_result in a SINGLE user message - splitting them across messages
        # trains the model to stop making parallel calls.
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f" -> Calling tool: {block.name}({block.input})")
                result = execute_tool(block.name, block.input)
                print(f" -> Result: {result}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,  # must match the tool_use block's id
                    "content": result,
                })

        messages.append({"role": "user", "content": tool_results})

    # Fell out of the loop without a final answer.
    return "Sorry, I couldn't complete that request (hit the iteration limit)."


if __name__ == "__main__":
    # Order 4821 exists in mock_orders, so this triggers one tool call and then
    # a natural-language reply.
    print(run_agent("Where is my order 4821, and when will it arrive?"))
