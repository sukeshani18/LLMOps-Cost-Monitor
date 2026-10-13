
import csv
import os
from datetime import datetime, timezone

CSV_FILE = "usage_logs.csv"

FIELDS = [
    "timestamp",
    "model",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "input_cost_usd",
    "output_cost_usd",
    "total_cost_usd",
]


def log_usage(result):
    """Append one successful LLM request to the usage CSV."""

    file_exists = (
        os.path.exists(CSV_FILE)
        and os.path.getsize(CSV_FILE) > 0
    )

    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": result["model"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "total_tokens": result["total_tokens"],
        "input_cost_usd": result["input_cost_usd"],
        "output_cost_usd": result["output_cost_usd"],
        "total_cost_usd": result["total_cost_usd"],
    }

    with open(
        CSV_FILE,
        mode="a",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=FIELDS,
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)

    print(f"Usage record saved to {CSV_FILE}")