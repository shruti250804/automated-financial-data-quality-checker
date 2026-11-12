-- 1. Exceptions by validation check
SELECT check_name, severity, COUNT(*) AS exception_count
FROM quality_exceptions
GROUP BY check_name, severity
ORDER BY exception_count DESC;

-- 2. Exception details for high-severity issues
SELECT record_id, rule_id, check_name, field, value, message
FROM quality_exceptions
WHERE severity = 'High'
ORDER BY record_id;

-- 3. Expense analysis by department
SELECT
    department,
    ROUND(SUM(CASE WHEN account_type = 'Expense' THEN amount ELSE 0 END), 2) AS expense_amount
FROM financial_transactions
GROUP BY department
ORDER BY expense_amount DESC;

-- 4. Budget vs actual variance by department
SELECT
    department,
    ROUND(SUM(amount), 2) AS actual_amount,
    ROUND(SUM(budget_amount), 2) AS budget_amount,
    ROUND(SUM(amount - budget_amount), 2) AS variance
FROM financial_transactions
GROUP BY department
ORDER BY ABS(variance) DESC;

-- 5. Payment reconciliation by status
SELECT
    status,
    COUNT(*) AS transaction_count,
    ROUND(SUM(invoice_total), 2) AS invoice_total,
    ROUND(SUM(paid_amount), 2) AS paid_amount,
    ROUND(SUM(invoice_total - paid_amount), 2) AS outstanding_amount
FROM financial_transactions
GROUP BY status;
