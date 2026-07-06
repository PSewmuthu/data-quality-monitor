# Data Quality Monitoring System (DQMS)

A fully automated Python system that monitors data integrity across datasets,
fires structured alerts, generates health reports, and serves a live HTML dashboard.

---

## Deliverables

| Deliverable                    | Location                            |
| ------------------------------ | ----------------------------------- |
| Automated DQ monitoring system | `monitor.py` + `core/`              |
| Data health dashboard          | `output/dq_dashboard.html`          |
| Alert reports                  | `output/dq_alerts_<timestamp>.csv`  |
| JSON audit report              | `output/dq_report_<timestamp>.json` |

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Regenerate fresh sample data and re-run
python monitor.py --generate

# 3. Open the dashboard
#    Open output/dq_dashboard.html in any browser

## Run the monitor (uses existing sample data)
python monitor.py
```

---

## Project Structure

```
dqms/
├── monitor.py                  ← CLI entry point
├── core/
│   ├── config.py               ← Schemas, thresholds, alert rules
│   ├── metrics.py              ← 6-dimension quality engine
│   ├── checks.py               ← Orchestrator
│   ├── alerts.py               ← Alert evaluation
│   ├── reporter.py             ← JSON / CSV report writer
│   └── dashboard_builder.py   ← Live dashboard injection
├── data/
│   ├── candidates.csv
│   ├── job_postings.csv
│   ├── applications.csv
│   └── generate_sample_data.py
├── output/
│   ├── dq_dashboard.html       ← Live-updated dashboard
│   └── reports
│       ├── dq_report_<ts>.json
│       ├── dq_summary_<ts>.csv
│       └── dq_alerts_<ts>.csv
└── docs/
    └── governance_framework.md ← Full governance documentation
```

---

## Quality Dimensions Monitored

| #   | Dimension        | What it checks                                             |
| --- | ---------------- | ---------------------------------------------------------- |
| 1   | **Completeness** | Fill rate on required fields                               |
| 2   | **Uniqueness**   | Primary key and full-row duplicates                        |
| 3   | **Validity**     | Email, phone, category, numeric range, date, regex pattern |
| 4   | **Consistency**  | Date ordering, salary min ≤ max, foreign key integrity     |
| 5   | **Timeliness**   | Record freshness vs. configurable max-age window           |
| 6   | **Accuracy**     | Statistical outlier detection via 3×IQR fences             |

---

## Alert Severity Levels

| Level       | Trigger                                  | Response SLA      |
| ----------- | ---------------------------------------- | ----------------- |
| 🔴 CRITICAL | System score < 75                        | Within 4 hours    |
| 🟠 HIGH     | Missing required fields, high duplicates | Same business day |
| 🟡 MEDIUM   | Format violations, stale data            | Within 48 hours   |
| 🔵 LOW      | Minor issues                             | Next sprint       |

---

## CLI Options

```
python monitor.py [OPTIONS]

Options:
  --data PATH      Folder containing CSV files (default: data/)
  --output PATH    Output folder for reports (default: output/)
  --generate       Regenerate sample data before running
  --max-age DAYS   Timeliness freshness window in days (default: 365)
```

---

## Outputs Per Run

1. **Console report** — colour-coded dimension scores per dataset
2. **`dq_dashboard.html`** — interactive HTML dashboard (auto-updated)
3. **`dq_report_<ts>.json`** — full audit-trail JSON
4. **`dq_summary_<ts>.csv`** — per-dataset score summary
5. **`dq_alerts_<ts>.csv`** — active alerts with severity and messages

---

## Governance Documentation

See [`docs/governance_framework.md`](docs/governance_framework.md) for:

- Data quality standards and thresholds
- Data stewardship roles and RACI matrix
- Alert escalation procedures
- Remediation workflows
- Retention and compliance policy
- Improvement recommendations

---
