import os
from dotenv import load_dotenv
from langsmith import traceable, Client

load_dotenv()

if not os.getenv("LANGSMITH_API_KEY"):
    raise ValueError("LANGSMITH_API_KEY is missing from your .env file")

if os.getenv("LANGSMITH_TRACING", "").lower() != "true":
    raise ValueError("Set LANGSMITH_TRACING=true in your .env file")

client = Client()

# Demonstration prices per million tokens (USD)
INPUT_PRICE_PER_MILLION = 2.00
OUTPUT_PRICE_PER_MILLION = 8.00


@traceable(
    name="LLM Cost Calculation",
    project_name="llmops-cost-monitor",
    tags=["cost-management", "test"]
)
def traced_cost_calculation(input_tokens, output_tokens):
    input_cost = (
        input_tokens / 1_000_000
    ) * INPUT_PRICE_PER_MILLION

    output_cost = (
        output_tokens / 1_000_000
    ) * OUTPUT_PRICE_PER_MILLION

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost_usd": round(input_cost, 8),
        "output_cost_usd": round(output_cost, 8),
        "total_cost_usd": round(input_cost + output_cost, 8),
    }


if __name__ == "__main__":
    result = traced_cost_calculation(2000, 1000)

    print("LangSmith trace test completed.")
    print(f"Input tokens: {result['input_tokens']}")
    print(f"Output tokens: {result['output_tokens']}")
    print(f"Estimated cost: ${result['total_cost_usd']:.6f}")

    client.flush()
