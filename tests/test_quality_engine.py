import pandas as pd
from quality_engine import normalize_data, run_quality_checks, build_summary

def make_df():
    return pd.DataFrame([
        {
            "transaction_id":"T1","transaction_date":"2025-01-01","account_type":"Expense",
            "category":"Software","department":"Technology","vendor":"A","amount":1000,
            "currency":"INR","status":"Paid","invoice_total":1000,"paid_amount":1000,"budget_amount":1100
        },
        {
            "transaction_id":"T1","transaction_date":"bad-date","account_type":"Expense",
            "category":"Software","department":"Technology","vendor":"B","amount":-500,
            "currency":"INR","status":"Paid","invoice_total":5000,"paid_amount":8000,"budget_amount":600
        }
    ])

def test_quality_engine_flags_expected_issues():
    raw = make_df()
    clean = normalize_data(raw)
    exc = run_quality_checks(raw, clean, invoice_tolerance=1000)
    checks = set(exc["check_name"])
    assert "Duplicate Transaction ID" in checks
    assert "Invalid Transaction Date" in checks
    assert "Negative Amount" in checks
    assert "Invoice Reconciliation" in checks
    assert "Paid Amount Exceeds Invoice" in checks

def test_summary_score_is_bounded():
    raw = make_df()
    exc = run_quality_checks(raw, normalize_data(raw))
    summary = build_summary(raw, exc)
    assert 0 <= summary["quality_score"] <= 100
    assert summary["rows_checked"] == 2
