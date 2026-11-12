import io
import sqlite3
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "transaction_id",
    "transaction_date",
    "account_type",
    "category",
    "department",
    "vendor",
    "amount",
    "currency",
    "status",
    "invoice_total",
    "paid_amount",
    "budget_amount",
]

APPROVED = {
    "account_type": {"Revenue", "Expense"},
    "category": {
        "Product Sales", "Services", "Subscription",
        "Marketing", "Software", "Travel", "Payroll", "Office"
    },
    "department": {"Finance", "Sales", "Operations", "Technology", "Marketing"},
    "currency": {"INR", "USD", "EUR", "GBP"},
    "status": {"Paid", "Pending", "Approved"},
}

def load_data(source):
    name = getattr(source, "name", str(source)).lower()
    if name.endswith(".csv"):
        return pd.read_csv(source)
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(source, sheet_name=0)
    raise ValueError("Only CSV, XLSX and XLS files are supported.")

def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    for col in ["transaction_id", "account_type", "category", "department", "vendor", "currency", "status"]:
        if col in out.columns:
            out[col] = out[col].astype("string").str.strip()

    if "currency" in out:
        out["currency"] = out["currency"].str.upper()

    # Conservative normalization: only obvious whitespace/case standardization.
    mapping = {
        "software": "Software",
        "product sales": "Product Sales",
        "services": "Services",
        "subscription": "Subscription",
        "marketing": "Marketing",
        "travel": "Travel",
        "payroll": "Payroll",
        "office": "Office",
    }
    if "category" in out:
        out["category"] = out["category"].map(
            lambda x: mapping.get(str(x).strip().lower(), x) if pd.notna(x) else x
        )

    if "transaction_date" in out:
        out["transaction_date"] = pd.to_datetime(out["transaction_date"], errors="coerce")

    for col in ["amount", "invoice_total", "paid_amount", "budget_amount"]:
        if col in out:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    return out

def _exception(row_num, record_id, rule_id, check_name, severity, field, value, message):
    return {
        "row_number": int(row_num),
        "record_id": "" if pd.isna(record_id) else str(record_id),
        "rule_id": rule_id,
        "check_name": check_name,
        "severity": severity,
        "field": field,
        "value": "" if pd.isna(value) else str(value),
        "message": message,
    }

def run_quality_checks(
    raw_df: pd.DataFrame,
    clean_df: pd.DataFrame,
    invoice_tolerance: float = 1000.0,
    iqr_multiplier: float = 1.5,
) -> pd.DataFrame:
    exceptions = []
    critical = ["transaction_id", "transaction_date", "account_type", "category", "department", "amount"]

    # Completeness
    for col in critical:
        raw = raw_df[col] if col in raw_df else pd.Series(index=raw_df.index, dtype="object")
        mask = raw.isna() | raw.astype("string").str.strip().eq("")
        for idx in raw_df.index[mask]:
            rid = raw_df.at[idx, "transaction_id"] if "transaction_id" in raw_df else ""
            exceptions.append(_exception(idx + 2, rid, "DQ001", "Missing Critical Field", "High", col, raw_df.at[idx, col], f"{col} is required."))

    # Duplicate ID
    dup_mask = raw_df["transaction_id"].astype("string").duplicated(keep=False)
    for idx in raw_df.index[dup_mask]:
        exceptions.append(_exception(idx + 2, raw_df.at[idx, "transaction_id"], "DQ002", "Duplicate Transaction ID", "High", "transaction_id", raw_df.at[idx, "transaction_id"], "Transaction ID is not unique."))

    # Invalid dates based on normalized parse
    invalid_dates = clean_df["transaction_date"].isna() & raw_df["transaction_date"].notna()
    for idx in raw_df.index[invalid_dates]:
        exceptions.append(_exception(idx + 2, raw_df.at[idx, "transaction_id"], "DQ003", "Invalid Transaction Date", "High", "transaction_date", raw_df.at[idx, "transaction_date"], "Transaction date could not be parsed."))

    # Consistency against approved master values
    rule_map = {
        "account_type": ("DQ004", "Inconsistent Account Type"),
        "category": ("DQ005", "Inconsistent Category"),
        "department": ("DQ006", "Inconsistent Department"),
        "currency": ("DQ007", "Inconsistent Currency"),
        "status": ("DQ008", "Inconsistent Status"),
    }
    for col, (rule_id, check_name) in rule_map.items():
        if col not in clean_df:
            continue
        mask = clean_df[col].notna() & ~clean_df[col].isin(APPROVED[col])
        for idx in clean_df.index[mask]:
            exceptions.append(_exception(idx + 2, raw_df.at[idx, "transaction_id"], rule_id, check_name, "Medium", col, raw_df.at[idx, col], f"Value is outside the approved {col} master list."))

    # Negative amount
    mask = clean_df["amount"].notna() & (clean_df["amount"] < 0)
    for idx in clean_df.index[mask]:
        exceptions.append(_exception(idx + 2, raw_df.at[idx, "transaction_id"], "DQ009", "Negative Amount", "High", "amount", raw_df.at[idx, "amount"], "Negative financial amount requires review."))

    # IQR numerical anomaly
    valid = clean_df["amount"].dropna()
    if len(valid) >= 4:
        q1, q3 = valid.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower = q1 - iqr_multiplier * iqr
        upper = q3 + iqr_multiplier * iqr
        mask = clean_df["amount"].notna() & ((clean_df["amount"] < lower) | (clean_df["amount"] > upper))
        for idx in clean_df.index[mask]:
            exceptions.append(_exception(
                idx + 2, raw_df.at[idx, "transaction_id"], "DQ010", "Numerical Outlier", "Medium", "amount",
                raw_df.at[idx, "amount"], f"Amount is outside IQR thresholds ({lower:,.2f} to {upper:,.2f})."
            ))

    # Invoice reconciliation
    diff = (clean_df["invoice_total"] - clean_df["amount"]).abs()
    mask = diff.notna() & (diff > invoice_tolerance)
    for idx in clean_df.index[mask]:
        exceptions.append(_exception(
            idx + 2, raw_df.at[idx, "transaction_id"], "DQ011", "Invoice Reconciliation", "Medium", "invoice_total",
            raw_df.at[idx, "invoice_total"], f"Invoice differs from transaction amount by ₹{diff.loc[idx]:,.2f}, above tolerance."
        ))

    # Paid > invoice
    diff_paid = clean_df["paid_amount"] - clean_df["invoice_total"]
    mask = diff_paid.notna() & (diff_paid > invoice_tolerance)
    for idx in clean_df.index[mask]:
        exceptions.append(_exception(
            idx + 2, raw_df.at[idx, "transaction_id"], "DQ012", "Paid Amount Exceeds Invoice", "High", "paid_amount",
            raw_df.at[idx, "paid_amount"], f"Paid amount exceeds invoice total by ₹{diff_paid.loc[idx]:,.2f}."
        ))

    columns = ["row_number","record_id","rule_id","check_name","severity","field","value","message"]
    return pd.DataFrame(exceptions, columns=columns)

def build_summary(raw_df: pd.DataFrame, exceptions: pd.DataFrame) -> Dict[str, float]:
    rows_checked = len(raw_df)
    affected = exceptions["row_number"].nunique() if not exceptions.empty else 0
    high = int((exceptions["severity"] == "High").sum()) if not exceptions.empty else 0
    exception_count = len(exceptions)
    quality_score = 100.0 if rows_checked == 0 else max(0.0, 100.0 * (1 - affected / rows_checked))
    return {
        "rows_checked": rows_checked,
        "exception_count": exception_count,
        "affected_rows": affected,
        "high_severity": high,
        "quality_score": quality_score,
    }

def load_to_sqlite(clean_df: pd.DataFrame, exceptions: pd.DataFrame, db_path) -> None:
    db_path = str(db_path)
    sql_df = clean_df.copy()
    if "transaction_date" in sql_df:
        sql_df["transaction_date"] = sql_df["transaction_date"].astype("string")
    with sqlite3.connect(db_path) as conn:
        sql_df.to_sql("financial_transactions", conn, if_exists="replace", index=False)
        exceptions.to_sql("quality_exceptions", conn, if_exists="replace", index=False)

def export_excel_report(clean_df: pd.DataFrame, exceptions: pd.DataFrame, summary: Dict[str, float]) -> bytes:
    buffer = io.BytesIO()
    summary_df = pd.DataFrame([
        ["Rows Checked", summary["rows_checked"]],
        ["Exception Count", summary["exception_count"]],
        ["Affected Rows", summary["affected_rows"]],
        ["High Severity Exceptions", summary["high_severity"]],
        ["Data Quality Score (%)", round(summary["quality_score"], 2)],
    ], columns=["Metric", "Value"])

    rules_df = pd.DataFrame([
        ["DQ001","Missing Critical Field","High","Critical fields cannot be blank"],
        ["DQ002","Duplicate Transaction ID","High","Transaction ID must be unique"],
        ["DQ003","Invalid Transaction Date","High","Date must be parseable"],
        ["DQ004-DQ008","Reference Data Consistency","Medium","Values must match approved master lists"],
        ["DQ009","Negative Amount","High","Negative amount requires review"],
        ["DQ010","Numerical Outlier","Medium","IQR-based anomaly detection"],
        ["DQ011","Invoice Reconciliation","Medium","Invoice and transaction amount must reconcile within tolerance"],
        ["DQ012","Paid Amount Exceeds Invoice","High","Paid amount should not materially exceed invoice"],
    ], columns=["Rule ID","Check","Severity","Rule"])

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        exceptions.to_excel(writer, sheet_name="Exceptions", index=False)
        clean_df.to_excel(writer, sheet_name="Cleaned Data", index=False)
        rules_df.to_excel(writer, sheet_name="Validation Rules", index=False)

        for ws in writer.book.worksheets:
            ws.freeze_panes = "A2"
            for cell in ws[1]:
                cell.font = cell.font.copy(bold=True)
            for column_cells in ws.columns:
                max_len = max(len(str(c.value)) if c.value is not None else 0 for c in column_cells)
                ws.column_dimensions[column_cells[0].column_letter].width = min(max(max_len + 2, 12), 42)

    return buffer.getvalue()

def generate_ai_prompt(prompt_type: str, exception: Optional[dict] = None, sql_text: str = "") -> str:
    disclaimer = (
        "You are assisting with financial data analysis. Do not invent facts. "
        "Use only the supplied information. Flag assumptions and recommend manual verification."
    )
    if prompt_type == "Explain exceptions" and exception:
        return f"""{disclaimer}

Explain this data-quality exception to a finance analyst in concise business language:
Rule: {exception.get('rule_id')}
Check: {exception.get('check_name')}
Record: {exception.get('record_id')}
Field: {exception.get('field')}
Value: {exception.get('value')}
System message: {exception.get('message')}

Return:
1. Why it matters
2. Likely causes
3. Verification steps
4. Recommended correction
"""
    if prompt_type == "Draft reconciliation commentary" and exception:
        return f"""{disclaimer}

Draft professional reconciliation commentary for this exception:
Record: {exception.get('record_id')}
Check: {exception.get('check_name')}
Details: {exception.get('message')}

Keep it factual and suitable for an exception report. Do not claim the issue is resolved unless evidence is provided.
"""
    return f"""{disclaimer}

Review the following SQLite query for correctness, readability, and performance.
Database tables:
- financial_transactions
- quality_exceptions

SQL:
{sql_text}

Return:
1. Corrected SQL if needed
2. Explanation of changes
3. Validation checks I should perform against the underlying data
"""
