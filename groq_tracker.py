
import os

from dotenv import load_dotenv
from groq import Groq
from langsmith import traceable, get_current_run_tree
from usage_logger import log_usage

# Load environment variables
load_dotenv()

# Model configuration
MODEL_NAME = "openai/gpt-oss-20b"

# Configured prices per million tokens (USD).
# Verify current rates on the Groq pricing page.
INPUT_PRICE_PER_MILLION = 0.075
OUTPUT_PRICE_PER_MILLION = 0.30


# Validate API keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing. Check your .env file.")

if not LANGSMITH_API_KEY:
    raise ValueError("LANGSMITH_API_KEY is missing. Check your .env file.")


# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)


def calculate_llm_cost(input_tokens, output_tokens):
    """Calculate estimated costs using configured token prices."""

    input_cost = (
        input_tokens / 1_000_000
    ) * INPUT_PRICE_PER_MILLION

    output_cost = (
        output_tokens / 1_000_000
    ) * OUTPUT_PRICE_PER_MILLION

    return {
        "input_cost_usd": input_cost,
        "output_cost_usd": output_cost,
        "total_cost_usd": input_cost + output_cost,
    }


@traceable(
    name="Groq LLM Request",
    run_type="llm",
    project_name="llmops-cost-monitor",
    metadata={
        "ls_provider": "groq",
        "ls_model_name": MODEL_NAME,
    },
    tags=["llmops", "cost-monitoring"],
)
def ask_groq(question):
    """Send a question to Groq and capture usage and costs."""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. "
                    "Answer the user's question clearly and concisely. "
                    "Return the answer as ordinary readable text."
                ),
            },
            {
                "role": "user",
                "content": question,
            },
        ],
        max_tokens=300,
    )

    # Extract the first response choice
    choice = response.choices[0]
    message = choice.message

    # Diagnostic information for investigating empty responses
    print("\n--- Response Diagnostics ---")
    print("Finish reason:", choice.finish_reason)
    print("Message:", message)
    print("Usage:", response.usage)

    # Extract answer text
    answer = message.content

    # Handle an empty or missing content field
    if not answer or not answer.strip():
        print(
            "Warning: The model returned empty message content. "
            "Check the diagnostic output above."
        )

        # Preserve any available message details for investigation.
        answer = (
            message.model_dump_json(indent=2)
        )

    # Actual token usage reported by Groq
    usage = response.usage

    input_tokens = usage.prompt_tokens
    output_tokens = usage.completion_tokens
    total_tokens = usage.total_tokens

    # Calculate estimated cost
    costs = calculate_llm_cost(
        input_tokens,
        output_tokens,
    )

    result = {
        "answer": answer,
        "model": MODEL_NAME,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "input_cost_usd": costs["input_cost_usd"],
        "output_cost_usd": costs["output_cost_usd"],
        "total_cost_usd": costs["total_cost_usd"],
    }

    # Attach usage and estimated cost metadata to LangSmith
    run = get_current_run_tree()

    if run is not None:
        run.set(
            usage_metadata={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "input_cost": costs["input_cost_usd"],
                "output_cost": costs["output_cost_usd"],
                "total_cost": costs["total_cost_usd"],
            }
        )

    return result


if __name__ == "__main__":
    print("=" * 45)
    print("       LLMOps Cost Monitoring System")
    print("=" * 45)

    question = input("\nEnter your question: ").strip()

    if not question:
        print("Please enter a question.")
    else:
        try:
            result = ask_groq(question)

            # Save the successful request's usage and estimated cost
            log_usage(result)

            print("\n--- Groq Response ---")
            print(result["answer"])

            print("\n--- Actual Token Usage ---")
            print(f"Model:         {result['model']}")
            print(f"Input tokens:  {result['input_tokens']}")
            print(f"Output tokens: {result['output_tokens']}")
            print(f"Total tokens:  {result['total_tokens']}")

            print("\n--- Estimated API Cost (USD) ---")
            print(f"Input cost:  ${result['input_cost_usd']:.8f}")
            print(f"Output cost: ${result['output_cost_usd']:.8f}")
            print(f"Total cost:  ${result['total_cost_usd']:.8f}")

        except Exception as error:
            print(f"\nRequest failed: {error}")