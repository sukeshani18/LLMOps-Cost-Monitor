

import csv
import os
from collections import defaultdict
from datetime import datetime, timezone

CSV_FILE = "usage_logs.csv"


def load_usage():
    """Load real usage records from the CSV file."""

    if not os.path.exists(CSV_FILE):
        print(f"Usage file not found: {CSV_FILE}")
        print("Run groq_cost_tracker.py to record a real request first.")
        return []

    with open(CSV_FILE, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        records = list(reader)

    valid_records = []

    for row in records:
        try:
            row["input_tokens"] = int(row["input_tokens"])
            row["output_tokens"] = int(row["output_tokens"])
            row["total_tokens"] = int(row["total_tokens"])
            row["input_cost_usd"] = float(row["input_cost_usd"])
            row["output_cost_usd"] = float(row["output_cost_usd"])
            row["total_cost_usd"] = float(row["total_cost_usd"])

            valid_records.append(row)

        except (ValueError, TypeError, KeyError):
            print("Warning: Skipping an invalid CSV record.")

    return valid_records


def print_usage_report(records):
    """Print a report based on recorded API requests."""

    print("\nLLM USAGE MONITORING REPORT")
    print("=" * 85)

    if not records:
        print("No valid usage records found.")
        return 0.0

    print(
        f"{'No.':<6}{'Model':<25}{'Input':>10}"
        f"{'Output':>10}{'Total':>10}{'Cost (USD)':>15}"
    )
    print("-" * 85)

    total_tokens = 0
    total_cost = 0.0

    for number, record in enumerate(records, start=1):
        total_tokens += record["total_tokens"]
        total_cost += record["total_cost_usd"]

        print(
            f"{number:<6}"
            f"{record['model'][:24]:<25}"
            f"{record['input_tokens']:>10,}"
            f"{record['output_tokens']:>10,}"
            f"{record['total_tokens']:>10,}"
            f"{record['total_cost_usd']:>15.8f}"
        )

    print("-" * 85)
    print(f"Total requests: {len(records)}")
    print(f"Total input tokens: {sum(r['input_tokens'] for r in records):,}")
    print(f"Total output tokens: {sum(r['output_tokens'] for r in records):,}")
    print(f"Total tokens: {total_tokens:,}")
    print(f"Total estimated cost: ${total_cost:.8f}")
    print(f"Average cost per request: ${total_cost / len(records):.8f}")

    return total_cost


def check_budget(current_cost, budget_limit):
    """Compare recorded estimated cost with a user-defined budget."""

    remaining = budget_limit - current_cost

    print("\nBUDGET MONITOR")
    print("-" * 35)
    print(f"Budget limit: ${budget_limit:.4f}")
    print(f"Recorded estimated cost: ${current_cost:.8f}")

    if remaining < 0:
        print(f"ALERT: Budget exceeded by ${abs(remaining):.8f}")
    elif remaining == 0:
        print("ALERT: Budget limit reached!")
    else:
        print(f"Remaining budget: ${remaining:.8f}")


def calculate_daily_costs(records):
    """Group recorded costs by UTC calendar date."""

    daily_costs = defaultdict(float)

    for record in records:
        try:
            timestamp = datetime.fromisoformat(
                record["timestamp"].replace("Z", "+00:00")
            )

            # Treat timestamps without a timezone as UTC.
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            date_key = timestamp.astimezone(timezone.utc).date().isoformat()
            daily_costs[date_key] += record["total_cost_usd"]

        except (ValueError, TypeError, KeyError):
            print("Warning: Skipping a record with an invalid timestamp.")

    return daily_costs


def forecast_monthly_cost(records, days=30):
    """Forecast costs from observed daily usage."""

    print("\nMONTHLY COST FORECAST")
    print("-" * 35)

    if not records:
        print("Not enough data to forecast.")
        return None

    daily_costs = calculate_daily_costs(records)

    if not daily_costs:
        print("No valid dated usage records are available.")
        return None

    # Include days with no requests in the observed calendar span.
    dates = [
        datetime.fromisoformat(date).date()
        for date in daily_costs
    ]
    observed_days = (max(dates) - min(dates)).days + 1

    total_recorded_cost = sum(daily_costs.values())
    average_daily_cost = total_recorded_cost / observed_days
    forecast = average_daily_cost * days

    print(f"Observed calendar days: {observed_days}")
    print(f"Total recorded cost: ${total_recorded_cost:.8f}")
    print(f"Average cost per calendar day: ${average_daily_cost:.8f}")
    print(f"Forecast period: {days} days")
    print(f"Projected cost: ${forecast:.8f}")

    if observed_days == 1:
        print(
            "Note: This forecast uses only one calendar day's usage; "
            "it may not represent typical future usage."
        )

    return forecast


if __name__ == "__main__":
    records = load_usage()

    if records:
        total_cost = print_usage_report(records)

        try:
            monthly_budget = float(
                input("\nEnter your usage budget in USD: $").strip()
            )

            if monthly_budget < 0:
                print("Budget cannot be negative.")
            else:
                check_budget(total_cost, monthly_budget)

        except ValueError:
            print("Invalid budget. Please enter a number.")

        forecast = forecast_monthly_cost(records)

        if forecast is not None:
            try:
                forecast_budget = float(
                    input("Enter your forecast budget in USD: $").strip()
                )

                if forecast_budget < 0:
                    print("Budget cannot be negative.")
                else:
                    check_budget(forecast, forecast_budget)

            except ValueError:
                print("Invalid forecast budget. Please enter a number.")
    else:
        print("\nNo report generated because no valid usage records were found.")