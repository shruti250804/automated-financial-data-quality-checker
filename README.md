# 🔍 Automated Financial Data Quality Checker

A fully functioning **Financial Data Quality & Reconciliation application** built using **Python, Excel, SQL, Streamlit, and Plotly**.

Designed as a portfolio project for **Associate Data Analyst, Financial Data Analyst, Data Quality Analyst, MIS Analyst, and Finance Operations** roles.

## 🚀 Live Demo

👉 **[View Live Automated Financial Data Quality Checker](https://automated-financial-data-quality-checker-jkffaxdchghujxb4k3rk4.streamlit.app/)**

---

## 📌 Project Overview

Financial reporting depends on accurate and consistent source data. This project provides an automated validation workflow that identifies data-quality problems before financial information is used for reporting or analysis.

The application validates financial transactions, assigns exceptions by severity, calculates an overall **Data Quality Score**, performs reconciliation checks, stores analytical data in SQLite, and generates downloadable exception reports.

---

## 🔎 Data Quality Checks

The application automatically checks for:

* Missing critical fields
* Duplicate transaction IDs
* Invalid transaction dates
* Inconsistent account types
* Inconsistent categories
* Inconsistent departments
* Invalid currencies
* Invalid workflow statuses
* Negative financial amounts
* Numerical anomalies using IQR-based outlier detection
* Invoice-to-transaction reconciliation differences
* Paid amounts materially exceeding invoice totals

---

## 📊 Dashboard Features

### Executive Summary

Provides management-level metrics including:

* Rows Checked
* Total Exceptions
* Affected Records
* High-Severity Exceptions
* Overall Data Quality Score

### Exception Reporting

Each detected issue contains:

* Transaction/Record ID
* Validation Rule
* Severity
* Affected Field
* Problematic Value
* Exception Description

Exception reports can be filtered and downloaded for further investigation.

### Financial Reconciliation

The application compares:

* Transaction Amount
* Invoice Total
* Paid Amount
* Budget Amount

This helps identify potential reconciliation differences and unusual financial transactions.

### SQL Analysis

Validated financial transactions and detected exceptions are stored in **SQLite**, allowing users to perform ad-hoc SQL analysis directly from the application.

### AI-Assisted Analysis

The application generates structured prompts that can be used with tools such as **ChatGPT or Microsoft Copilot** for:

* Explaining data-quality exceptions
* Drafting reconciliation commentary
* Reviewing SQL queries

Financial data is **not automatically sent to an external AI provider**, and AI-generated results should be manually verified before business use.

### Data Export

Users can download:

* Full Excel Data Quality Report
* Exception Report
* Cleaned Financial Dataset
* CSV output

---

## 🛠️ Technology Stack

| Technology           | Purpose                                         |
| -------------------- | ----------------------------------------------- |
| **Python**           | Validation engine and financial data processing |
| **Pandas**           | Data cleaning and transformation                |
| **SQL / SQLite**     | Data storage and analytical querying            |
| **Excel / OpenPyXL** | Financial exception report generation           |
| **Streamlit**        | Interactive web application                     |
| **Plotly**           | Interactive visualizations                      |
| **Pytest**           | Automated testing                               |
| **GitHub**           | Version control and project hosting             |

---

## 📁 Project Structure

```text
automated_financial_data_quality_checker/
│
├── app.py
├── quality_engine.py
├── requirements.txt
├── README.md
│
├── data/
│   └── financial_transactions_sample.xlsx
│
├── docs/
│   └── validation_rules.md
│
├── sql/
│   └── analysis_queries.sql
│
└── tests/
    └── test_quality_engine.py
```

---

## 💻 Run Locally in VS Code

### 1. Clone the repository

```bash
git clone https://github.com/titlydey/automated-financial-data-quality-checker.git
```

### 2. Open the project

```bash
cd automated-financial-data-quality-checker
```

### 3. Create a virtual environment

```powershell
py -m venv .venv
```

### 4. Activate the environment

```powershell
.venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```powershell
py -m pip install -r requirements.txt
```

### 6. Run automated tests

```powershell
py -m pytest -q
```

Expected result:

```text
2 passed
```

### 7. Start the application

```powershell
py -m streamlit run app.py
```

The application will normally open at:

```text
http://localhost:8501
```

---

## 📂 Sample Financial Dataset

The repository includes:

```text
data/financial_transactions_sample.xlsx
```

The dataset contains deliberately inserted data-quality exceptions so the validation engine can demonstrate detection and reporting.

### Required Columns

```text
transaction_id
transaction_date
account_type
category
department
vendor
amount
currency
status
invoice_total
paid_amount
budget_amount
```

Users can also upload their own compatible **CSV or Excel dataset** directly through the Streamlit interface.

---

## 🗄️ SQL Analysis

When the application runs, it creates:

```text
finance_quality.db
```

with two primary tables:

```text
financial_transactions
quality_exceptions
```

Example query:

```sql
SELECT
    check_name,
    severity,
    COUNT(*) AS exception_count
FROM quality_exceptions
GROUP BY check_name, severity
ORDER BY exception_count DESC;
```

Additional SQL examples are available in:

```text
sql/analysis_queries.sql
```

---

## 🧪 Data Quality Methodology

The validation engine combines several types of controls.

**Completeness Checks**
Identify missing critical financial information.

**Uniqueness Checks**
Detect duplicate transaction IDs.

**Validity Checks**
Identify invalid dates and unexpected reference-data values.

**Financial Controls**
Identify negative amounts and invoice/payment reconciliation differences.

**Anomaly Detection**
Uses the **Interquartile Range (IQR)** method to identify unusually high or low transaction amounts.

**Reference Data Validation**
Checks account types, categories, departments, currencies, and transaction statuses against approved values.

---

## 💼 Business Problem

Financial reports can become unreliable when source transactions contain missing values, duplicates, invalid dates, inconsistent master data, unusual amounts, or reconciliation differences.

These problems can lead to inaccurate reporting and additional manual reconciliation work.

---

## 💡 Solution

The project creates a repeatable data-quality workflow:

**Financial Dataset → Data Cleaning → Validation Rules → Exception Detection → Reconciliation → SQLite → Dashboard → Excel Reporting**

This allows analysts to identify problematic transactions before they are used for financial reporting and business decision-making.

---

## 🎯 Business Value

The application demonstrates how automated data-quality controls can:

* Improve financial reporting accuracy
* Reduce manual validation effort
* Accelerate reconciliation
* Identify high-risk exceptions
* Standardize validation rules
* Improve auditability
* Support data-driven financial analysis

---

## 🤖 Responsible AI Usage

AI is used only as an **assisted productivity layer**.

The application generates structured prompts for analytical explanations and SQL review but does not automatically transmit financial data to an external AI provider.

All AI-generated output should be compared against:

* Source financial data
* Documented validation rules
* Reconciliation evidence
* Business requirements

before being used for decision-making.

---

## 🎯 Skills Demonstrated

**Data Analytics:** Python, Pandas, Excel, SQL

**Data Quality:** Validation, Completeness, Uniqueness, Consistency and Exception Management

**Financial Analysis:** Transaction Analysis, Invoice Reconciliation and Budget Comparison

**Database:** SQLite and SQL Analysis

**Visualization:** Streamlit and Plotly

**Automation:** Automated Validation and Excel Reporting

**Testing:** Pytest

**AI Productivity:** Structured AI-assisted analytical workflows with manual verification

---

## 📄 Resume Description

**Automated Financial Data Quality Checker | Python, Excel, SQL, Streamlit**

* Built an automated financial data-quality checker to detect missing values, duplicate transactions, invalid dates, reference-data inconsistencies, numerical anomalies, and financial reconciliation exceptions.
* Developed rule-based exception reporting, financial reconciliation controls, data-quality scoring, SQLite analysis tables, and downloadable Excel/CSV reports.
* Implemented IQR-based anomaly detection and documented validation rules to support repeatable financial data-quality controls.
* Added an AI-assisted productivity layer for exception explanations and SQL review with manual verification before business use.

---

## 🚀 Live Project

**Streamlit:**
https://automated-financial-data-quality-checker-jkffaxdchghujxb4k3rk4.streamlit.app/

**GitHub:**
https://github.com/titlydey/automated-financial-data-quality-checker

---

## 👩‍💻 Author

**Title Dey**

B.Tech Computer Science & Engineering
Data Analytics | SQL | Excel | Tableau | Python

LinkedIn: linkedin.com/in/titlydey
