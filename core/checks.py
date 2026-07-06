'''
checks.py - Automated Data Quality Checks
Runs all 6 dimension checks on each dataset.
'''
import pandas as pd
from datetime import datetime
from typing import Dict

from .metrics import (
    check_completeness, check_uniqueness, check_validity,
    check_consistency, check_timeliness, check_accuracy
)
from .config import SCHEMAS, THRESHOLDS, OVERALL_THRESHOLD


def _classify(score: float, thresholds: dict) -> str:
    if score < thresholds["critical"]:
        return "CRITICAL"
    if score < thresholds["warning"]:
        return "WARNING"
    if score < thresholds["good"]:
        return "GOOD"

    return "EXCELLENT"


def run_checks(datasets: Dict[str, pd.DataFrame], max_age_days: int = 365) -> dict:
    '''
    Run full DQ suite on all provided datasets.
    datasets: {"candidates": df, "job_postings": df, ...}
    Returns structured results dict ready for reporting / dashboard.
    '''
    run_time = datetime.now().isoformat(timespec='seconds')
    all_results = {}

    for name, df in datasets.items():
        if name not in SCHEMAS:
            print(
                f"[SKIP] No schema defined for dataset '{name}'. Skipping checks.")
            continue

        schema = SCHEMAS[name]
        print(
            f"  Checking '{name}' ({len(df)} rows, {len(df.columns)} cols)...")

        completeness = check_completeness(df, schema)
        uniqueness = check_uniqueness(df, schema)
        validity = check_validity(df, schema)
        consistency = check_consistency(df, schema, all_dfs=datasets)
        timeliness = check_timeliness(df, schema, max_age_days)
        accuracy = check_accuracy(df, schema)

        dim_scores = {
            "completeness":  completeness["score"],
            "uniqueness":    uniqueness["score"],
            "validity":      validity["score"],
            "consistency":   consistency["score"],
            "timeliness":    timeliness["score"],
            "accuracy":      accuracy["score"],
        }
        overall = round(sum(dim_scores.values()) / len(dim_scores), 2)

        all_results[name] = {
            "dataset":       name,
            "row_count":     len(df),
            "col_count":     len(df.columns),
            "run_time":      run_time,
            "overall_score": overall,
            "overall_status": _classify(overall, OVERALL_THRESHOLD),
            "dimensions": {
                "completeness":  {**dim_scores, **completeness,
                                  "status": _classify(completeness["score"], THRESHOLDS["completeness"])},
                "uniqueness":    {**uniqueness,
                                  "status": _classify(uniqueness["score"], THRESHOLDS["uniqueness"])},
                "validity":      {**validity,
                                  "status": _classify(validity["score"], THRESHOLDS["validity"])},
                "consistency":   {**consistency,
                                  "status": _classify(consistency["score"], THRESHOLDS["consistency"])},
                "timeliness":    {**timeliness,
                                  "status": _classify(timeliness["score"], THRESHOLDS["timeliness"])},
                "accuracy":      {**accuracy,
                                  "status": _classify(accuracy["score"], THRESHOLDS["accuracy"])},
            },
        }

    # Cross-dataset summary
    if all_results:
        scores = [r["overall_score"] for r in all_results.values()]
        system_score = round(sum(scores) / len(scores), 2)
    else:
        system_score = 0.0

    return {
        "run_time": run_time,
        "system_score": system_score,
        "system_status": _classify(system_score, OVERALL_THRESHOLD),
        "datasets": all_results
    }
