# Financial Data Quality Validation Rules

The checker applies documented controls before financial data is used for reporting or reconciliation.

| Rule | Control | Severity | Logic |
|---|---|---|---|
| DQ001 | Missing Critical Field | High | Required financial fields cannot be blank |
| DQ002 | Duplicate Transaction ID | High | Transaction IDs must be unique |
| DQ003 | Invalid Transaction Date | High | Dates must be parseable |
| DQ004-DQ008 | Reference Data Consistency | Medium | Account type, category, department, currency and status must match approved values |
| DQ009 | Negative Amount | High | Negative transaction amounts are flagged for review |
| DQ010 | Numerical Outlier | Medium | IQR method detects unusual financial amounts |
| DQ011 | Invoice Reconciliation | Medium | Invoice total must reconcile to transaction amount within user-defined tolerance |
| DQ012 | Paid Amount Exceeds Invoice | High | Paid amount cannot materially exceed invoice total |

## Manual verification

Automated controls identify exceptions. They do not determine the business cause. Each exception should be validated against source documents, approved master data, and finance policy before correction.

## AI-assisted workflow

The Streamlit application generates prompts for ChatGPT, Microsoft Copilot, or similar tools. It does not automatically send finance data to an external AI service. AI-generated explanations or SQL suggestions should be manually checked before use.
