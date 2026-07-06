# Data Governance Framework

## Data Quality Monitoring System

**Version:** 1.0  
**Prepared by:** P.S. Abewickrama Singhe
**Date:** July 2026  
**Classification:** Public

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Scope and Objectives](#2-scope-and-objectives)
3. [Data Quality Dimensions & Standards](#3-data-quality-dimensions--standards)
4. [Data Quality Metrics & Thresholds](#4-data-quality-metrics--thresholds)
5. [Automated Monitoring Architecture](#5-automated-monitoring-architecture)
6. [Alert Severity Framework](#6-alert-severity-framework)
7. [Data Stewardship Roles & Responsibilities](#7-data-stewardship-roles--responsibilities)
8. [Data Quality Improvement Procedures](#8-data-quality-improvement-procedures)
9. [Data Retention & Lifecycle Policy](#9-data-retention--lifecycle-policy)
10. [Compliance & Audit Trail](#10-compliance--audit-trail)
11. [Governance Recommendations](#11-governance-recommendations)
12. [Glossary](#12-glossary)

---

## 1. Executive Summary

This document establishes the **Data Governance Framework** for data ecosystem. It defines the standards, policies, roles, and automated procedures that ensure data integrity, reliability, and compliance across all datasets — including candidate profiles, job postings, and application records.

The framework is operationalised through the **Data Quality Monitoring System (DQMS)**, an automated Python-based pipeline that continuously evaluates six quality dimensions, fires structured alerts, and generates health reports for every monitored dataset.

**Key Governance Principles:**

| Principle                  | Description                                                 |
| -------------------------- | ----------------------------------------------------------- |
| **Accuracy**               | Data reflects real-world facts without distortion           |
| **Consistency**            | The same data means the same thing across all systems       |
| **Accountability**         | Every dataset has a named owner responsible for its quality |
| **Transparency**           | Quality scores and issues are visible to all stakeholders   |
| **Continuous Improvement** | Alert-driven feedback loops drive measurable quality gains  |

---

## 2. Scope and Objectives

### 2.1 In-Scope Datasets

| Dataset        | Description                                                      | Estimated Volume |
| -------------- | ---------------------------------------------------------------- | ---------------- |
| `candidates`   | Candidate personal data, skills, experience, application history | ~300+ records    |
| `job_postings` | Job listings with requirements, salary bands, and deadlines      | ~80+ records     |
| `applications` | Many-to-many link between candidates and job postings            | ~500+ records    |

### 2.2 Governance Objectives

1. Define measurable quality standards for all data fields.
2. Automate detection of data quality violations before they impact business decisions.
3. Establish clear ownership and escalation paths for quality issues.
4. Produce auditable quality health reports on every monitoring run.
5. Reduce time-to-detection of data integrity issues from days to minutes.

### 2.3 Out of Scope

- Third-party job board data (not ingested into internal systems).
- Payroll and financial records (governed by the Finance Data Policy).
- Employee records post-placement (governed by HR Policy).

---

## 3. Data Quality Dimensions & Standards

The DQMS evaluates six internationally recognised data quality dimensions (ISO 8000 / DAMA-DMBOK aligned):

### 3.1 Completeness

**Definition:** The proportion of required data fields that contain non-null, non-empty values.

**Why it matters:** Incomplete candidate records prevent proper matching. Missing salary fields lead to incorrect shortlisting.

**Standard:** All fields marked `required: true` in the schema must achieve ≥ 95% fill rate. Optional fields must achieve ≥ 80%.

**Measurement:**

```
Fill Rate (%) = (Non-null values / Total records) × 100
```

**Required fields per dataset:**

| Dataset      | Required Fields                                                                                                       |
| ------------ | --------------------------------------------------------------------------------------------------------------------- |
| candidates   | `candidate_id`, `first_name`, `last_name`, `email`, `years_experience`, `applied_date`, `status`, `job_title_applied` |
| job_postings | `job_id`, `title`, `sector`, `min_experience`, `min_salary`, `posted_date`, `closing_date`, `is_active`               |
| applications | `application_id`, `candidate_id`, `job_id`, `application_date`, `stage`                                               |

---

### 3.2 Uniqueness

**Definition:** The absence of duplicate records, particularly for primary key fields.

**Why it matters:** Duplicate candidate IDs cause double-counting in reports. Duplicate applications skew hiring funnel analytics.

**Standard:** Primary key fields must have 0% duplication. Full-row duplicates must be < 1%.

**Measurement:**

```
Uniqueness Score (%) = (Non-duplicate primary key values / Total records) × 100
```

**Primary keys:** `candidate_id`, `job_id`, `application_id`

---

### 3.3 Validity

**Definition:** Data values conform to defined formats, patterns, and allowed value sets.

**Why it matters:** Invalid phone numbers prevent candidate contact. Out-of-range salary values corrupt compensation benchmarks.

**Standard:** ≥ 96% of non-null values must pass their defined validation rule.

**Validation rules by field type:**

| Type               | Validation Rule                             | Example                                                             |
| ------------------ | ------------------------------------------- | ------------------------------------------------------------------- |
| `email`            | RFC 5322 format                             | `name@domain.com`                                                   |
| `phone_lk`         | Sri Lanka 10-digit (0XXXXXXXXX)             | `0771234567`                                                        |
| `categorical`      | Must be in allowed value set                | `status ∈ {Applied, Screened, Interview, Offered, Hired, Rejected}` |
| `numeric`          | Within defined min/max range                | `years_experience ∈ [0, 50]`                                        |
| `date`             | Parseable as ISO 8601 or common date format | `2025-01-15`                                                        |
| `boolean`          | True/False/1/0                              | `is_active = True`                                                  |
| `string + pattern` | Matches regex pattern                       | `candidate_id ~ ^C\d{4}$`                                           |

---

### 3.4 Consistency

**Definition:** Data values are logically coherent within a record and across related datasets.

**Why it matters:** A job posting where `closing_date < posted_date` is logically impossible. An application referencing a non-existent `candidate_id` breaks referential integrity.

**Standard:** ≥ 95% of cross-field and cross-dataset consistency checks must pass.

**Consistency rules enforced:**

| Rule                    | Check                                                 | Datasets                    |
| ----------------------- | ----------------------------------------------------- | --------------------------- |
| Date ordering           | `posted_date ≤ closing_date`                          | job_postings                |
| Salary ordering         | `min_salary ≤ max_salary`                             | job_postings                |
| Experience ordering     | `min_experience ≤ max_experience`                     | job_postings                |
| Foreign key — candidate | `applications.candidate_id ∈ candidates.candidate_id` | applications → candidates   |
| Foreign key — job       | `applications.job_id ∈ job_postings.job_id`           | applications → job_postings |

---

### 3.5 Timeliness

**Definition:** Data is current and available within the expected time window.

**Why it matters:** Job postings that have not been updated in over a year may be stale. Candidate records with application dates far in the past may no longer be active.

**Standard:** ≥ 92% of dated records must fall within the configured freshness window (default: 365 days).

**Measurement:**

```
Age of Record = Current Date − Date Field Value
Timeliness Score (%) = (Records with Age ≤ max_age_days / Total dated records) × 100
```

**Date fields monitored:** `applied_date` (candidates), `posted_date` / `closing_date` (job_postings), `application_date` (applications).

---

### 3.6 Accuracy

**Definition:** Numeric data values are statistically plausible — i.e., free from extreme outliers that likely indicate data entry errors.

**Why it matters:** A candidate with 99 years of experience or a salary of LKR 0 signals data entry errors that corrupt analytics and shortlisting algorithms.

**Standard:** ≥ 97% of numeric values must fall within the 3×IQR (interquartile range) statistical fence.

**Measurement:**

```
Lower Fence = Q1 − 3 × IQR
Upper Fence = Q3 + 3 × IQR
Accuracy Score (%) = (Values within fences / Total numeric values) × 100
```

**Numeric fields monitored:** `years_experience`, `salary_expectation`, `min_salary`, `max_salary`, `min_experience`, `max_experience`, `applications_count`.

---

## 4. Data Quality Metrics & Thresholds

### 4.1 Dimension Thresholds

Each dimension has three threshold levels that drive status classification and alert triggering:

| Dimension    | CRITICAL (< x) | WARNING (< x) | GOOD (< x) | EXCELLENT |
| ------------ | -------------- | ------------- | ---------- | --------- |
| Completeness | 70             | 85            | 95         | ≥ 95      |
| Uniqueness   | 90             | 95            | 99         | ≥ 99      |
| Validity     | 75             | 88            | 96         | ≥ 96      |
| Consistency  | 70             | 85            | 95         | ≥ 95      |
| Timeliness   | 60             | 80            | 92         | ≥ 92      |
| Accuracy     | 80             | 90            | 97         | ≥ 97      |

### 4.2 Overall System Score

The **Overall Dataset Score** is the unweighted mean of all six dimension scores. The **System Score** is the mean across all monitored datasets.

| System Score | Status    | Interpretation                                                           |
| ------------ | --------- | ------------------------------------------------------------------------ |
| ≥ 93         | EXCELLENT | Data is highly reliable; no immediate action needed                      |
| 85–92        | GOOD      | Minor issues present; investigate during next sprint                     |
| 75–84        | WARNING   | Significant issues; data steward must act within 48 hours                |
| < 75         | CRITICAL  | Data unreliable; business decisions should be paused pending remediation |

---

## 5. Automated Monitoring Architecture

### 5.1 System Components

```
dqms/
├── monitor.py              ← Entry point / CLI runner
├── core/
│   ├── config.py           ← Schemas, thresholds, alert rules
│   ├── metrics.py          ← 6-dimension calculation engine
│   ├── checks.py           ← Orchestrator — runs all dimensions per dataset
│   ├── alerts.py           ← Alert evaluation and formatting
│   ├── reporter.py         ← JSON, CSV, and console report generation
│   └── dashboard_builder.py← Live data injection into HTML dashboard
├── data/
│   ├── candidates.csv
│   ├── job_postings.csv
│   └── applications.csv
└── output/
    ├── dq_dashboard.html   ← Live-updated HTML dashboard
    └── reports
        ├── dq_report_<ts>.json ← Full timestamped JSON report
        ├── dq_summary_<ts>.csv ← Per-dataset summary CSV
        └── dq_alerts_<ts>.csv  ← Active alerts CSV
```

### 5.2 Execution Flow

```
1. Load CSV datasets from data/ directory
       ↓
2. Run 6-dimension quality checks per dataset (core/metrics.py)
       ↓
3. Compute overall scores and status classifications (core/checks.py)
       ↓
4. Evaluate alert rules against dimension scores (core/alerts.py)
       ↓
5. Print colour-coded console report
       ↓
6. Save timestamped JSON + CSV reports to output/
       ↓
7. Inject live data into dq_dashboard.html (core/dashboard_builder.py)
```

### 5.3 Running the Monitor

```bash
# Standard run (uses existing data)
python monitor.py

# Regenerate sample data then run
python monitor.py --generate

# Custom data folder
python monitor.py --data /path/to/your/csvs/

# Custom timeliness window (180-day freshness)
python monitor.py --max-age 180

# Custom output folder
python monitor.py --output /path/to/reports/
```

### 5.4 Scheduling (Recommended)

For production environments, schedule the monitor using:

**Windows Task Scheduler:**

```
Action: python C:\path\to\dqms\monitor.py
Schedule: Daily at 07:00 AM
```

**Linux/macOS Cron:**

```bash
0 7 * * * cd /path/to/dqms && python monitor.py >> logs/dqms.log 2>&1
```

---

## 6. Alert Severity Framework

### 6.1 Severity Levels

| Level    | Icon | Meaning                                | Response SLA               |
| -------- | ---- | -------------------------------------- | -------------------------- |
| CRITICAL | 🔴   | System score < 75 or uniqueness < 90   | Immediate — within 4 hours |
| HIGH     | 🟠   | Missing key fields or high duplication | Same business day          |
| MEDIUM   | 🟡   | Format violations or stale data        | Within 48 hours            |
| LOW      | 🔵   | Minor issues, informational            | Next sprint                |
| INFO     | ⚪   | Advisory notices                       | No action required         |

### 6.2 Alert Rules

| Rule Name                      | Condition                                  | Severity       |
| ------------------------------ | ------------------------------------------ | -------------- |
| Critical Overall Score         | `overall_score < 75`                       | CRITICAL       |
| High Duplicate Rate            | `uniqueness_score < 90`                    | HIGH           |
| Missing Key Fields             | `completeness_score < 85`                  | HIGH           |
| Invalid Formats                | `validity_score < 88`                      | MEDIUM         |
| Stale Data                     | `timeliness_score < 80`                    | MEDIUM         |
| Consistency Drift              | `consistency_score < 85`                   | MEDIUM         |
| Low Fill Rate (Required Field) | `fill_rate < 80` on any required column    | HIGH or MEDIUM |
| Column Validity Issue          | `column_validity_score < 85` with examples | MEDIUM         |

### 6.3 Alert Escalation Path

```
Alert Generated
      ↓
  CRITICAL / HIGH → Data Steward notified immediately
      ↓
  Not resolved in SLA → Data Owner escalated
      ↓
  Systemic issue → Data Governance Committee review
```

---

## 7. Data Stewardship Roles & Responsibilities

### 7.1 Role Definitions

| Role              | Responsibilities                                                                                         |
| ----------------- | -------------------------------------------------------------------------------------------------------- |
| **Data Owner**    | Accountable for a dataset's business accuracy. Approves schema changes. Resolves CRITICAL alerts.        |
| **Data Steward**  | Operationally monitors daily DQ scores. Triages alerts. Coordinates remediation. Reviews weekly reports. |
| **Data Engineer** | Maintains the DQMS codebase. Adds new checks as business rules evolve. Deploys schema updates.           |
| **Data Consumer** | Uses data for hiring analytics and reporting. Reports anomalies noticed in downstream outputs.           |

### 7.2 Dataset Ownership Matrix

| Dataset      | Data Owner                 | Data Steward        |
| ------------ | -------------------------- | ------------------- |
| candidates   | Head of Talent Acquisition | Coordinator         |
| job_postings | Head of Client Services    | Job Listing Manager |
| applications | Head of Talent Acquisition | Coordinator         |

### 7.3 RACI Matrix

| Activity                 | Data Owner | Data Steward | Data Engineer | Data Consumer |
| ------------------------ | ---------- | ------------ | ------------- | ------------- |
| Define quality standards | A          | R            | C             | I             |
| Run daily monitoring     | I          | A            | R             | I             |
| Triage MEDIUM alerts     | I          | A            | C             | I             |
| Resolve CRITICAL alerts  | A          | R            | C             | I             |
| Update schema / rules    | A          | C            | R             | I             |
| Review weekly report     | R          | A            | I             | I             |
| Approve schema changes   | A          | C            | R             | I             |

_R = Responsible, A = Accountable, C = Consulted, I = Informed_

---

## 8. Data Quality Improvement Procedures

### 8.1 Remediation Workflow

When an alert is triggered:

1. **Identify** — Read the alert message for dataset, dimension, score, and examples.
2. **Isolate** — Open `dq_report_<timestamp>.json` → drill into the flagged column/check.
3. **Root-cause** — Was it a data entry error, a system migration, or a schema mismatch?
4. **Fix** — Correct the source data or update the validation rule if the rule was wrong.
5. **Re-run** — Execute `python monitor.py` to verify the score improved.
6. **Document** — Record the issue and fix in the remediation log (see below).

### 8.2 Remediation Log Template

| Date | Alert ID | Dataset | Dimension | Root Cause | Action Taken | Score Before | Score After | Resolved By |
| ---- | -------- | ------- | --------- | ---------- | ------------ | ------------ | ----------- | ----------- |
|      |          |         |           |            |              |              |             |             |

### 8.3 Common Issues & Fixes

| Issue                   | Likely Cause                                          | Recommended Fix                                                                         |
| ----------------------- | ----------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Invalid phone numbers   | Data entered without leading zero or with spaces      | Add input validation at data entry point; run `phone.str.replace(r'\s+','',regex=True)` |
| Duplicate candidate IDs | Manual data import without deduplication              | Add `UNIQUE` constraint at source; run `df.drop_duplicates(subset=['candidate_id'])`    |
| Stale job postings      | `closing_date` not updated when re-posted             | Implement a re-posting flag; update `closing_date` on every repost                      |
| Missing `applied_date`  | Bulk import from external system without date mapping | Map source system timestamp field during ETL                                            |
| Orphaned applications   | Candidate or job deleted after application created    | Enforce foreign key constraints at database level                                       |

---

## 9. Data Retention & Lifecycle Policy

### 9.1 Retention Schedule

| Dataset                          | Retention Period                     | Basis               |
| -------------------------------- | ------------------------------------ | ------------------- |
| Active candidate profiles        | Indefinite while candidate is active | Business need       |
| Inactive candidate profiles      | 2 years after last activity          | PDPA Sri Lanka 2022 |
| Job postings (closed)            | 3 years                              | Audit requirement   |
| Application records              | 3 years                              | Employment law      |
| DQ monitoring reports (JSON/CSV) | 1 year rolling                       | Internal audit      |
| Alerts CSV                       | 1 year rolling                       | Internal audit      |

### 9.2 Data Disposal

Data exceeding retention must be:

1. Permanently deleted from production systems.
2. Purged from all backup snapshots within 30 days.
3. Recorded in the Data Disposal Register with date and approver.

### 9.3 Archiving

Data approaching retention limits but needed for analytics should be:

- Anonymised (remove PII: name, email, phone, NIC).
- Archived to a secure read-only cold storage location.
- Flagged with `archived = True` to exclude from live DQ checks.

---

## 10. Compliance & Audit Trail

### 10.1 Regulatory Alignment

| Regulation              | Relevance                                                      | How DQMS Supports                                        |
| ----------------------- | -------------------------------------------------------------- | -------------------------------------------------------- |
| **PDPA Sri Lanka 2022** | Candidate personal data must be accurate, current, and minimal | Completeness + Accuracy checks flag inaccurate/stale PII |
| **ISO 8000**            | International data quality standard                            | 6 dimension framework aligns with ISO 8000 Part 61       |
| **DAMA-DMBOK**          | Data management best practice                                  | Stewardship roles and RACI follow DMBOK Chapter 13       |

### 10.2 Audit Trail

Every monitoring run produces a timestamped JSON report (`dq_report_YYYYMMDD_HHMMSS.json`) containing:

- Run timestamp
- System and per-dataset scores
- All dimension details with column-level breakdown
- All alerts fired with messages and scores

These reports constitute the **data quality audit trail** and must be retained for 1 year.

### 10.3 Evidence of Compliance

To demonstrate data governance compliance in an audit:

1. Present the `output/dq_report_<date>.json` for the period in question.
2. Show the `output/dq_alerts_<date>.csv` to demonstrate issues were detected.
3. Show the remediation log to demonstrate issues were resolved.
4. Present this document as evidence of the governance framework.

---

## 11. Governance Recommendations

Based on the initial system deployment, the following improvements are recommended:

### Priority 1 — Immediate (This Quarter)

| #   | Recommendation                                                                                       | Benefit                                                        | Effort |
| --- | ---------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | ------ |
| 1.1 | **Fix phone number validation at entry point** — enforce 10-digit format in the data collection form | Eliminates majority of current MEDIUM alerts on phone validity | Low    |
| 1.2 | **Schedule daily monitoring** using Task Scheduler or cron                                           | Shifts from reactive to proactive quality management           | Low    |
| 1.3 | **Assign named Data Stewards** for each dataset                                                      | Creates accountability; ensures alerts are actioned within SLA | Low    |
| 1.4 | **Implement unique constraints on primary keys** at the data entry level                             | Prevents duplicate records before they enter the system        | Medium |

### Priority 2 — Short-Term (Next Quarter)

| #   | Recommendation                                                                                 | Benefit                                                | Effort |
| --- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ------ |
| 2.1 | **Email alert integration** — send CRITICAL/HIGH alerts to the Data Steward automatically      | Reduces time-to-detection from next-run to real-time   | Medium |
| 2.2 | **Add `updated_at` timestamp to all tables**                                                   | Enables precise timeliness tracking per record         | Medium |
| 2.3 | **Build a trend dashboard** — track DQ scores over time (week-on-week)                         | Reveals whether data quality is improving or degrading | Medium |
| 2.4 | **Extend schema to new datasets** as the system grows (e.g., interview records, offer letters) | Provides full pipeline coverage                        | High   |

### Priority 3 — Long-Term (6–12 Months)

| #   | Recommendation                                                                                   | Benefit                                                         | Effort |
| --- | ------------------------------------------------------------------------------------------------ | --------------------------------------------------------------- | ------ |
| 3.1 | **Database migration** — move from CSV to PostgreSQL with enforced constraints                   | Structural prevention is stronger than after-the-fact detection | High   |
| 3.2 | **Automated remediation rules** — auto-flag and quarantine records that fail critical checks     | Prevents bad data from entering downstream analytics            | High   |
| 3.3 | **Data lineage tracking** — record where each record came from (manual entry, CSV import, API)   | Critical for root-cause analysis of systemic issues             | High   |
| 3.4 | **Machine learning anomaly detection** — supplement IQR outlier detection with isolation forests | Catches subtle anomalies that rule-based checks miss            | High   |

---

## 12. Glossary

| Term                       | Definition                                                                                 |
| -------------------------- | ------------------------------------------------------------------------------------------ |
| **Data Governance**        | The set of policies, processes, and roles that ensure data is managed as a strategic asset |
| **Data Quality Dimension** | A measurable characteristic of data (e.g., completeness, accuracy)                         |
| **DQ Score**               | A 0–100 numeric score for a dataset on a specific dimension                                |
| **Schema**                 | The defined structure, types, and rules for a dataset's columns                            |
| **Primary Key**            | A column whose values uniquely identify each record (e.g., `candidate_id`)                 |
| **Foreign Key**            | A column that references the primary key of another dataset                                |
| **Fill Rate**              | The percentage of non-null values in a column                                              |
| **IQR**                    | Interquartile Range — the spread between the 25th and 75th percentile                      |
| **Data Steward**           | The person operationally responsible for a dataset's day-to-day quality                    |
| **Data Owner**             | The person business-accountable for a dataset's accuracy and use                           |
| **PDPA**                   | Personal Data Protection Act — Sri Lanka's data privacy legislation (2022)                 |
| **DAMA-DMBOK**             | Data Management Body of Knowledge — global data management best practices guide            |
| **SLA**                    | Service Level Agreement — the maximum acceptable time to resolve an issue                  |
| **Remediation**            | The process of identifying, fixing, and verifying a data quality issue                     |
| **Audit Trail**            | Timestamped records of system activity used as evidence in compliance reviews              |

---
