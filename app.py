
import os

import pandas as pd
import streamlit as st

CSV_FILE = "usage_logs.csv"

st.set_page_config(
    page_title="LLMOps Cost Monitor",
    page_icon="💰",
    layout="wide",
)

st.title("LLMOps Cost Monitor")
st.caption("API cost estimates and usage log management")

# Budget configuration
st.subheader("Budget Settings")

budget = st.number_input(
    "Budget limit (USD)",
    min_value=0.0,
    value=10.0,
    step=1.0,
    format="%.2f",
)

st.divider()

# Load usage records
if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
    st.info(
        "No usage records found yet. Submit a prompt in the LLM Playground "
        "to generate usage data."
    )
    st.stop()

try:
    df = pd.read_csv(CSV_FILE)
except (pd.errors.EmptyDataError, pd.errors.ParserError, OSError) as error:
    st.error(f"Unable to read usage logs: {error}")
    st.stop()

required_columns = [
    "model",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "input_cost_usd",
    "output_cost_usd",
    "total_cost_usd",
]

if not all(column in df.columns for column in required_columns):
    st.error("The usage CSV is missing required columns.")
    st.stop()

for column in required_columns[1:]:
    df[column] = pd.to_numeric(df[column], errors="coerce")

df = df.dropna(
    subset=[
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "input_cost_usd",
        "output_cost_usd",
        "total_cost_usd",
    ]
)

if df.empty:
    st.warning("No valid usage records found.")
    st.stop()

# Cost calculations
total_requests = len(df)
input_tokens = int(df["input_tokens"].sum())
output_tokens = int(df["output_tokens"].sum())
total_tokens = int(df["total_tokens"].sum())

input_cost = float(df["input_cost_usd"].sum())
output_cost = float(df["output_cost_usd"].sum())
total_cost = float(df["total_cost_usd"].sum())

average_cost = total_cost / total_requests
remaining_budget = budget - total_cost

# Cost summary
st.subheader("Cost Summary")

col1, col2, col3 = st.columns(3)

col1.metric("Total Requests", f"{total_requests:,}")
col2.metric("Total Estimated Cost", f"${total_cost:.8f}")
col3.metric("Average Cost per Request", f"${average_cost:.8f}")

st.subheader("Cost Breakdown")

cost_col1, cost_col2 = st.columns(2)

cost_col1.metric("Input Cost", f"${input_cost:.8f}")
cost_col2.metric("Output Cost", f"${output_cost:.8f}")

st.subheader("Token Usage")

token_col1, token_col2, token_col3 = st.columns(3)

token_col1.metric("Input Tokens", f"{input_tokens:,}")
token_col2.metric("Output Tokens", f"{output_tokens:,}")
token_col3.metric("Total Tokens", f"{total_tokens:,}")

st.divider()

# Budget status
st.subheader("Budget Status")

budget_col1, budget_col2 = st.columns(2)

budget_col1.metric("Budget Limit", f"${budget:.2f}")
budget_col2.metric("Budget Remaining", f"${remaining_budget:.8f}")

if budget == 0:
    st.info("Set a budget greater than zero to monitor your spending limit.")
elif remaining_budget < 0:
    st.error(f"Budget exceeded by ${abs(remaining_budget):.8f}.")
elif total_cost >= budget * 0.8:
    st.warning("At least 80% of your configured budget has been used.")
else:
    st.success("Estimated spending is within your configured budget.")

st.divider()

# Download original usage logs
st.subheader("Usage Log Management")

st.write(
    "Download the complete usage log to archive it or import it into "
    "Microsoft Power BI for further analysis."
)

with open(CSV_FILE, "rb") as file:
    csv_data = file.read()

st.download_button(
    label="Download Usage Logs (CSV)",
    data=csv_data,
    file_name="usage_logs.csv",
    mime="text/csv",
    use_container_width=True,
)

st.caption(
    "All costs are estimates based on the pricing rates configured in "
    "the backend. They may differ from actual provider billing."
)

