import io
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from quality_engine import (
    REQUIRED_COLUMNS,
    load_data,
    run_quality_checks,
    build_summary,
    export_excel_report,
    load_to_sqlite,
    normalize_data,
    generate_ai_prompt,
)

st.set_page_config(
    page_title="Automated Financial Data Quality Checker",
    page_icon="✅",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_FILE = BASE_DIR / "data" / "financial_transactions_sample.xlsx"
DB_FILE = BASE_DIR / "finance_quality.db"

st.title("✅ Automated Financial Data Quality Checker")
st.caption("Python • Excel • SQL • Data Quality • Reconciliation • Exception Reporting")

with st.sidebar:
    st.header("Data Source")
    uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])
    st.info("No file? The included sample financial dataset loads automatically.")
    st.divider()
    st.header("Validation Settings")
    tolerance = st.number_input(
        "Invoice reconciliation tolerance (₹)",
        min_value=0.0,
        value=1000.0,
        step=100.0
    )
    outlier_multiplier = st.slider(
        "IQR outlier sensitivity",
        min_value=1.0,
        max_value=3.0,
        value=1.5,
        step=0.1
    )

source = uploaded if uploaded is not None else DEFAULT_FILE

try:
    raw_df = load_data(source)
except Exception as exc:
    st.error(f"Could not load data: {exc}")
    st.stop()

missing_cols = [c for c in REQUIRED_COLUMNS if c not in raw_df.columns]
if missing_cols:
    st.error("Missing required columns: " + ", ".join(missing_cols))
    st.stop()

clean_df = normalize_data(raw_df)
exceptions = run_quality_checks(
    raw_df,
    clean_df,
    invoice_tolerance=tolerance,
    iqr_multiplier=outlier_multiplier
)
summary = build_summary(raw_df, exceptions)

# Store latest data for SQL exploration
load_to_sqlite(clean_df, exceptions, DB_FILE)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Rows Checked", f"{summary['rows_checked']:,}")
c2.metric("Exceptions", f"{summary['exception_count']:,}")
c3.metric("Affected Rows", f"{summary['affected_rows']:,}")
c4.metric("High Severity", f"{summary['high_severity']:,}")
c5.metric("Data Quality Score", f"{summary['quality_score']:.1f}%")

tabs = st.tabs([
    "Executive Summary",
    "Exception Report",
    "Validation Rules",
    "SQL Analysis",
    "AI Assistant Prompts",
    "Data & Export"
])

with tabs[0]:
    left, right = st.columns(2)
    with left:
        st.subheader("Exceptions by Validation Check")
        if exceptions.empty:
            st.success("No exceptions found.")
        else:
            chart_data = exceptions["check_name"].value_counts().reset_index()
            chart_data.columns = ["check_name", "count"]
            fig = px.bar(chart_data, x="count", y="check_name", orientation="h")
            fig.update_layout(yaxis_title="", xaxis_title="Exceptions")
            st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Exceptions by Severity")
        if not exceptions.empty:
            sev = exceptions["severity"].value_counts().reset_index()
            sev.columns = ["severity", "count"]
            fig = px.pie(sev, names="severity", values="count", hole=0.45)
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Financial Reconciliation Snapshot")
    numeric_cols = ["amount", "invoice_total", "paid_amount", "budget_amount"]
    display = {}
    for col in numeric_cols:
        display[col] = pd.to_numeric(clean_df[col], errors="coerce").sum()
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Transaction Amount", f"₹{display['amount']:,.0f}")
    k2.metric("Invoice Total", f"₹{display['invoice_total']:,.0f}")
    k3.metric("Paid Amount", f"₹{display['paid_amount']:,.0f}")
    k4.metric("Budget Amount", f"₹{display['budget_amount']:,.0f}")

with tabs[1]:
    st.subheader("Exception Report")
    if exceptions.empty:
        st.success("No exceptions found for the current validation settings.")
    else:
        severity_filter = st.multiselect(
            "Severity",
            sorted(exceptions["severity"].dropna().unique()),
            default=sorted(exceptions["severity"].dropna().unique())
        )
        filtered = exceptions[exceptions["severity"].isin(severity_filter)]
        st.dataframe(filtered, use_container_width=True, hide_index=True)

        st.download_button(
            "Download Exception Report (CSV)",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="financial_data_quality_exceptions.csv",
            mime="text/csv"
        )

with tabs[2]:
    st.subheader("Validation Rules")
    rules = pd.DataFrame([
        ["DQ001", "Missing Critical Fields", "High", "Critical fields must not be blank."],
        ["DQ002", "Duplicate Transaction ID", "High", "Transaction IDs must be unique."],
        ["DQ003", "Invalid Transaction Date", "High", "Transaction dates must be parseable."],
        ["DQ004", "Inconsistent Category", "Medium", "Categories must match approved master values."],
        ["DQ005", "Inconsistent Department", "Medium", "Departments must match approved master values."],
        ["DQ006", "Inconsistent Currency", "Medium", "Currency must be one of the approved ISO values."],
        ["DQ007", "Inconsistent Status", "Medium", "Status must match the approved workflow values."],
        ["DQ008", "Negative Amount", "High", "Negative financial amounts are flagged for review."],
        ["DQ009", "Numerical Outlier", "Medium", "Amounts outside IQR thresholds are flagged."],
        ["DQ010", "Invoice Reconciliation", "Medium", "Invoice total should reconcile to amount within tolerance."],
        ["DQ011", "Paid > Invoice", "High", "Paid amount should not materially exceed invoice total."],
    ], columns=["Rule ID", "Check", "Severity", "Validation Logic"])
    st.dataframe(rules, use_container_width=True, hide_index=True)

with tabs[3]:
    st.subheader("Interactive SQL Analysis")
    st.caption("The cleaned data is stored in `financial_transactions`; exceptions are stored in `quality_exceptions`.")

    examples = {
        "Exceptions by check": """
SELECT check_name, severity, COUNT(*) AS exception_count
FROM quality_exceptions
GROUP BY check_name, severity
ORDER BY exception_count DESC;
""",
        "Department spending": """
SELECT department,
       ROUND(SUM(CASE WHEN account_type = 'Expense' THEN amount ELSE 0 END), 2) AS expense_amount
FROM financial_transactions
GROUP BY department
ORDER BY expense_amount DESC;
""",
        "Budget variance": """
SELECT department,
       ROUND(SUM(amount), 2) AS actual_amount,
       ROUND(SUM(budget_amount), 2) AS budget_amount,
       ROUND(SUM(amount - budget_amount), 2) AS variance
FROM financial_transactions
GROUP BY department
ORDER BY ABS(variance) DESC;
"""
    }
    query_name = st.selectbox("Example query", list(examples))
    sql = st.text_area("SQL", value=examples[query_name].strip(), height=180)
    if st.button("Run SQL Query"):
        try:
            with sqlite3.connect(DB_FILE) as conn:
                result = pd.read_sql_query(sql, conn)
            st.dataframe(result, use_container_width=True)
        except Exception as exc:
            st.error(f"SQL error: {exc}")

with tabs[4]:
    st.subheader("AI-Assisted Productivity Layer")
    st.write(
        "This section does not send data to an external AI service. It creates ready-to-use prompts "
        "for ChatGPT, Microsoft Copilot, or a similar tool. Review all AI output manually before using it."
    )
    prompt_type = st.selectbox(
        "Prompt type",
        ["Explain exceptions", "Draft reconciliation commentary", "Improve SQL query"]
    )

    selected_exception = None
    if not exceptions.empty and prompt_type != "Improve SQL query":
        row_labels = [
            f"{i}: {r['check_name']} | {r['record_id']} | {r['field']}"
            for i, r in exceptions.reset_index(drop=True).iterrows()
        ]
        chosen = st.selectbox("Choose an exception", row_labels)
        idx = int(chosen.split(":")[0])
        selected_exception = exceptions.reset_index(drop=True).iloc[idx].to_dict()

    sql_text = ""
    if prompt_type == "Improve SQL query":
        sql_text = st.text_area("SQL to review", "SELECT department, SUM(amount) FROM financial_transactions GROUP BY department;")

    prompt = generate_ai_prompt(prompt_type, selected_exception, sql_text)
    st.code(prompt, language=None)
    st.caption("Manual verification required: compare AI suggestions with source data, business rules, and reconciliation evidence.")

with tabs[5]:
    st.subheader("Cleaned Data")
    st.dataframe(clean_df, use_container_width=True, hide_index=True)

    report = export_excel_report(clean_df, exceptions, summary)
    st.download_button(
        "Download Full Excel Quality Report",
        data=report,
        file_name="financial_data_quality_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.download_button(
        "Download Cleaned Data (CSV)",
        data=clean_df.to_csv(index=False).encode("utf-8"),
        file_name="clean_financial_transactions.csv",
        mime="text/csv"
    )

with st.expander("Expected dataset columns"):
    st.code(", ".join(REQUIRED_COLUMNS))
