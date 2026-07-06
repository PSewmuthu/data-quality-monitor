'''
alerts.py - Data Quality Alert Engine
Evaluates ALERT_RULES against check results and emits structured alerts.
'''
from datetime import datetime
from typing import List, Dict
from .config import ALERT_RULES

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
SEVERITY_EMOJI = {"CRITICAL": "🔴", "HIGH": "🟠",
                  "MEDIUM": "🟡", "LOW": "🔵", "INFO": "⚪"}


def _eval_condition(condition: str, scores: dict) -> bool:
    """Safely evaluate a string condition like 'overall_score < 75'."""
    try:
        return eval(condition, {"__builtins__": {}}, scores)
    except Exception:
        return False


def generate_alerts(results: dict) -> List[Dict]:
    '''
    Takes the output of run_checks() and returns a sorted list of alerts.
    Each alert has: id, severity, dataset, rule_name, message, score, timestamp.
    '''
    alerts = []
    ts = datetime.now().isoformat(timespec='seconds')
    aid = 1

    for ds_name, ds_result in results["datasets"].items():
        dims = ds_result["dimensions"]

        scores_ctx = {
            "overall_score":      ds_result["overall_score"],
            "completeness_score": dims["completeness"]["score"],
            "uniqueness_score":   dims["uniqueness"]["score"],
            "validity_score":     dims["validity"]["score"],
            "consistency_score":  dims["consistency"]["score"],
            "timeliness_score":   dims["timeliness"]["score"],
            "accuracy_score":     dims["accuracy"]["score"],
        }

        for rule in ALERT_RULES:
            if _eval_condition(rule["condition"], scores_ctx):
                # Extract the score referenced in condition
                score_key = rule["condition"].split()[0]
                score_val = scores_ctx.get(score_key, 0)
                dim_name = score_key.replace("_score", "")
                threshold = rule["condition"].split()[-1]

                alerts.append({
                    "id":        f"ALT-{aid:03d}",
                    "timestamp": ts,
                    "severity":  rule["severity"],
                    "dataset":   ds_name,
                    "rule":      rule["name"],
                    "message":   (
                        f"[{ds_name.upper()}] {rule['name']}: "
                        f"{dim_name.capitalize()} score is {score_val:.1f} "
                        f"(threshold: {threshold})"
                    ),
                    "score":     score_val,
                    "dimension": dim_name,
                })
                aid += 1

        # Additional column-level alerts for completeness
        for col, detail in dims["completeness"].get("column_detail", {}).items():
            if detail.get("required") and detail.get("fill_rate", 100) < 80:
                alerts.append({
                    "id":        f"ALT-{aid:03d}",
                    "timestamp": ts,
                    "severity":  "HIGH" if detail["fill_rate"] < 60 else "MEDIUM",
                    "dataset":   ds_name,
                    "rule":      "Low Fill Rate on Required Field",
                    "message":   (
                        f"[{ds_name.upper()}] Column '{col}' fill rate is "
                        f"{detail['fill_rate']:.1f}% ({detail['missing_count']} missing)"
                    ),
                    "score":     detail["fill_rate"],
                    "dimension": "completeness",
                })
                aid += 1

        # Validity column alerts
        for col, detail in dims["validity"].get("column_detail", {}).items():
            if detail.get("score", 100) < 85 and detail.get("issue_examples"):
                alerts.append({
                    "id":        f"ALT-{aid:03d}",
                    "timestamp": ts,
                    "severity":  "MEDIUM",
                    "dataset":   ds_name,
                    "rule":      "Column Validity Issue",
                    "message":   (
                        f"[{ds_name.upper()}] Column '{col}': {detail['issue_examples'][0]}"
                    ),
                    "score":     detail["score"],
                    "dimension": "validity",
                })
                aid += 1

    # Sort by severity then score ascending
    alerts.sort(key=lambda a: (
        SEVERITY_ORDER.get(a["severity"], 99), a["score"]))
    return alerts


def print_alerts(alerts: List[Dict]) -> None:
    if not alerts:
        print("  ✅ No alerts generated — all checks passed!")
        return

    print(f"\n  {'─'*70}")
    print(f"  {'ACTIVE ALERTS':^70}")
    print(f"  {'─'*70}")

    for a in alerts:
        emoji = SEVERITY_EMOJI.get(a["severity"], "⚪")
        print(f"  {emoji} [{a['severity']:<8}] {a['id']}  {a['message']}")

    print(f"  {'─'*70}")
    counts = {}

    for a in alerts:
        counts[a["severity"]] = counts.get(a["severity"], 0) + 1

    summary = " | ".join(
        f"{SEVERITY_EMOJI[s]} {s}: {c}" for s, c in counts.items())
    print(f"  Total: {len(alerts)} alerts  —  {summary}")
