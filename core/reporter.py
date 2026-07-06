'''
reporter.py - Data Health Report Generator
Produces JSON summary + CSV drill-down reports.
'''
import os
import json
import csv
from datetime import datetime


def save_json_report(results: dict, alerts: list, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(output_dir, f"data_quality_report_{ts}.json")
    payload = {
        "report_metadata": {
            "generated_at":    results["run_time"],
            "system_score":    results["system_score"],
            "system_status":   results["system_status"],
            "total_datasets":  len(results["datasets"]),
            "total_alerts":    len(alerts),
        },
        "dataset_results": results["datasets"],
        "alerts":          alerts
    }

    with open(path, 'w') as f:
        json.dump(payload, f, indent=2, default=str)

    print(f"  📄 JSON report  → {path}")
    return path


def save_csv_summary(results: dict, alerts: list, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(output_dir, f"dq_summary_{ts}.csv")
    rows = []

    for ds_name, ds in results["datasets"].items():
        row = {
            "dataset":       ds_name,
            "rows":          ds["row_count"],
            "overall_score": ds["overall_score"],
            "overall_status": ds["overall_status"],
        }

        for dim, data in ds["dimensions"].items():
            row[f"{dim}_score"] = data.get("score", "")
            row[f"{dim}_status"] = data.get("status", "")

        rows.append(row)

    if rows:
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    print(f"  📊 CSV summary  → {path}")
    return path


def save_alerts_csv(alerts: list, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(output_dir, f"dq_alerts_{ts}.csv")

    if not alerts:
        return path

    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(alerts[0].keys()))
        w.writeheader()
        w.writerows(alerts)

    print(f"  🚨 Alerts CSV   → {path}")
    return path


def print_console_report(results: dict, alerts: list) -> None:
    WIDTH = 72
    BARS = {"EXCELLENT": "████████████", "GOOD": "█████████░░░",
            "WARNING":   "██████░░░░░░", "CRITICAL": "███░░░░░░░░░"}
    STATUS_COLOR = {"EXCELLENT": "\033[92m", "GOOD": "\033[96m",
                    "WARNING":   "\033[93m", "CRITICAL": "\033[91m"}
    RESET = "\033[0m"

    print("\n" + "═" * WIDTH)
    print(f"{'  DATA QUALITY MONITORING SYSTEM — GAMAGE RECRUITERS':^{WIDTH}}")
    print(f"{'  Run at: ' + results['run_time']:^{WIDTH}}")
    print("═" * WIDTH)

    sc = results["system_score"]
    st = results["system_status"]
    col = STATUS_COLOR.get(st, "")
    print(f"\n  SYSTEM OVERALL SCORE: {col}{sc:.1f} / 100  [{st}]{RESET}\n")

    for ds_name, ds in results["datasets"].items():
        print(f"  ┌{'─'*68}┐")
        print(f"  │  Dataset: {ds_name:<20}  Rows: {ds['row_count']:<6}  "
              f"Score: {ds['overall_score']:5.1f}  [{ds['overall_status']}]{' '*(5-len(ds['overall_status']))}  │")
        print(f"  ├{'─'*68}┤")

        for dim, data in ds["dimensions"].items():
            score = data.get("score", 0)
            status = data.get("status", "")
            col = STATUS_COLOR.get(status, "")
            bar = BARS.get(status, "░" * 12)
            print(
                f"  │  {dim:<14}  {bar}  {col}{score:5.1f}{RESET}  [{status}]{' '*(9-len(status))}    │")

        print(f"  └{'─'*68}┘\n")

    crit = sum(1 for a in alerts if a["severity"] == "CRITICAL")
    high = sum(1 for a in alerts if a["severity"] == "HIGH")
    med = sum(1 for a in alerts if a["severity"] == "MEDIUM")
    print(f"  Alerts fired: 🔴 CRITICAL {crit}  🟠 HIGH {high}  🟡 MEDIUM {med}")
    print("═" * WIDTH + "\n")
