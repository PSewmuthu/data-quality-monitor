'''
metrics.py - Data Quality Metrics Engine
Computes scores across 6 DQ dimensions for any DataFrame + schema.
'''
import re
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Tuple

# ===================================================================================================
#  Helpers
# ===================================================================================================
EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_LK = re.compile(r"^0[0-9]{9}$")           # Sri Lanka 10-digit


def _pct(num, den):
    return round(100 * num / den, 2) if den else 100.0


def _score(pass_count, total):
    return _pct(pass_count, total)


# ===================================================================================================
#  Dimension 1: Completeness
# ===================================================================================================
def check_completeness(df: pd.DataFrame, schema: dict) -> dict:
    '''Percentage of non-null values for each required (and optional) field.'''
    results = {}
    required_scores, all_scores = [], []

    for col, rules in schema["columns"].items():
        if col not in df.columns:
            results[col] = {"present": False, "fill_rate": 0.0, "missing_count": len(
                df), "required": rules.get("required", False)}
            if rules.get("required"):
                required_scores.append(0.0)
            all_scores.append(0.0)
            continue

        filled = df[col].notna().sum()
        fill_rt = _pct(filled, len(df))
        results[col] = {
            "present":      True,
            "fill_rate":    fill_rt,
            "missing_count": int(len(df) - filled),
            "required":     rules.get("required", False),
        }
        all_scores.append(fill_rt)
        if rules.get("required"):
            required_scores.append(fill_rt)

    overall = round(np.mean(required_scores), 2) if required_scores else round(
        np.mean(all_scores), 2)
    return {"score": overall, "column_detail": results}


# ===================================================================================================
#  Dimension 2: Uniqueness
# ===================================================================================================
def check_uniqueness(df: pd.DataFrame, schema: dict) -> dict:
    pk = schema.get("primary_key")
    results = {}

    # Primary key duplicates
    if pk and pk in df.columns:
        dup_mask = df.duplicated(subset=[pk], keep=False)
        dup_count = int(dup_mask.sum())
        dup_values = df.loc[dup_mask, pk].value_counts().head(5).to_dict()
        pk_score = _score(
            len(df) - int(df.duplicated(subset=[pk]).sum()), len(df))
        results["primary_key"] = {
            "column": pk, "duplicate_rows": dup_count,
            "duplicate_values": {str(k): int(v) for k, v in dup_values.items()},
            "score": pk_score,
        }
    else:
        pk_score = 100.0

    # Full-row duplicates
    full_dup = int(df.duplicated().sum())
    full_score = _score(len(df) - full_dup, len(df))
    results["full_row"] = {"duplicate_rows": full_dup, "score": full_score}

    overall = round((pk_score + full_score) / 2, 2)
    return {"score": overall, "detail": results}


# ===================================================================================================
#  Dimension 3: Validity
# ===================================================================================================
def _validate_column(series: pd.Series, rules: dict) -> Tuple[int, int, List[str]]:
    '''Returns (pass_count, total_non_null, list of issue examples).'''
    non_null = series.dropna()
    total = len(non_null)

    if total == 0:
        return 0, 0, []

    issues = []

    vtype = rules.get("type", "string")

    if vtype == "email":
        mask = non_null.astype(str).str.match(EMAIL_RE)
        bad = non_null[~mask].head(3).tolist()
        passes = int(mask.sum())

        if bad:
            issues.append(f"Invalid emails: {bad}")

        return passes, total, issues

    if vtype == "phone_lk":
        mask = non_null.astype(str).str.match(PHONE_LK)
        bad = non_null[~mask].head(3).tolist()
        passes = int(mask.sum())

        if bad:
            issues.append(f"Invalid phones: {bad}")

        return passes, total, issues

    if vtype == "categorical":
        allowed = set(rules.get("allowed", []))
        mask = non_null.isin(allowed)
        bad = non_null[~mask].head(3).tolist()
        passes = int(mask.sum())

        if bad:
            issues.append(f"Unknown categories: {bad}")

        return passes, total, issues

    if vtype == "numeric":
        numeric = pd.to_numeric(non_null, errors="coerce")
        valid = numeric.notna()
        mn, mx = rules.get("min"), rules.get("max")

        if mn is not None:
            valid &= (numeric >= mn)

        if mx is not None:
            valid &= (numeric <= mx)

        bad = non_null[~valid].head(3).tolist()
        passes = int(valid.sum())

        if bad:
            issues.append(f"Out-of-range/non-numeric: {bad}")

        return passes, total, issues

    if vtype == "date":
        def _try_parse(v):
            try:
                pd.to_datetime(v)
                return True
            except:
                return False

        mask = non_null.astype(str).apply(_try_parse)
        bad = non_null[~mask].head(3).tolist()
        passes = int(mask.sum())

        if bad:
            issues.append(f"Invalid dates: {bad}")

        return passes, total, issues

    if vtype == "boolean":
        valid_vals = {True, False, "True", "False",
                      "true", "false", 1, 0, "1", "0"}
        mask = non_null.apply(lambda x: x in valid_vals)
        passes = int(mask.sum())

        return passes, total, issues

    if vtype == "string" and "pattern" in rules:
        pat = re.compile(rules["pattern"])
        mask = non_null.astype(str).str.match(pat)
        bad = non_null[~mask].head(3).tolist()
        passes = int(mask.sum())

        if bad:
            issues.append(f"Pattern mismatch: {bad}")

        return passes, total, issues

    # default: all non-null pass
    return total, total, issues


def check_validity(df: pd.DataFrame, schema: dict) -> dict:
    results = {}
    col_scores = []

    for col, rules in schema["columns"].items():
        if col not in df.columns:
            continue

        passes, total, issues = _validate_column(df[col], rules)
        score = _score(passes, total) if total else 100.0
        results[col] = {
            "score":        score,
            "valid_count":  passes,
            "checked":      total,
            "issue_examples": issues,
        }
        col_scores.append(score)

    overall = round(np.mean(col_scores), 2) if col_scores else 100.0
    return {"score": overall, "column_detail": results}


# ===================================================================================================
#  Dimension 4: Consistency
# ===================================================================================================
def check_consistency(df: pd.DataFrame, schema: dict, all_dfs: dict = None) -> dict:
    results = {}
    scores = []

    # Date ordering checks
    date_cols = schema.get("date_columns", [])
    if len(date_cols) >= 2:
        for i in range(len(date_cols) - 1):
            c1, c2 = date_cols[i], date_cols[i + 1]
            if c1 in df.columns and c2 in df.columns:
                d1 = pd.to_datetime(df[c1], errors="coerce")
                d2 = pd.to_datetime(df[c2], errors="coerce")
                both = d1.notna() & d2.notna()
                ok = (d1[both] <= d2[both]).sum()
                tot = both.sum()
                s = _score(int(ok), int(tot)) if tot else 100.0
                results[f"{c1}_before_{c2}"] = {
                    "check": f"{c1} ≤ {c2}",
                    "pass_count": int(ok), "total": int(tot), "score": s
                }
                scores.append(s)

    # Numeric range consistency (min ≤ max for salary/experience)
    pairs = [("min_experience", "max_experience"),
             ("min_salary", "max_salary")]
    for c1, c2 in pairs:
        if c1 in df.columns and c2 in df.columns:
            both = df[c1].notna() & df[c2].notna()
            ok = (df.loc[both, c1] <= df.loc[both, c2]).sum()
            tot = both.sum()
            s = _score(int(ok), int(tot)) if tot else 100.0
            results[f"{c1}_le_{c2}"] = {
                "check": f"{c1} ≤ {c2}", "pass_count": int(ok), "total": int(tot), "score": s
            }
            scores.append(s)

    # Foreign key integrity
    fks = schema.get("foreign_keys", {})
    if fks and all_dfs:
        for fk_col, ref in fks.items():
            ref_ds, ref_col = ref.split(".")
            if ref_ds in all_dfs and fk_col in df.columns and ref_col in all_dfs[ref_ds].columns:
                valid_vals = set(all_dfs[ref_ds][ref_col].dropna().astype(str))
                actual = df[fk_col].dropna().astype(str)
                ok = actual.isin(valid_vals).sum()
                tot = len(actual)
                s = _score(int(ok), tot)
                results[f"fk_{fk_col}"] = {
                    "check": f"{fk_col} → {ref}", "pass_count": int(ok), "total": tot, "score": s,
                    "orphan_examples": actual[~actual.isin(valid_vals)].head(3).tolist()
                }
                scores.append(s)

    overall = round(np.mean(scores), 2) if scores else 100.0
    return {"score": overall, "checks": results}


# ===================================================================================================
#  Dimension 5: Timeliness
# ===================================================================================================
def check_timeliness(df: pd.DataFrame, schema: dict, max_age_days: int = 365) -> dict:
    date_cols = schema.get("date_columns", [])
    results = {}
    scores = []
    now = datetime.now()

    for col in date_cols:
        if col not in df.columns:
            continue

        parsed = pd.to_datetime(df[col], errors="coerce").dropna()
        if parsed.empty:
            continue

        ages = (now - parsed).dt.days
        fresh = (ages <= max_age_days).sum()
        score = _score(int(fresh), len(parsed))
        results[col] = {
            "score":          score,
            "median_age_days": int(ages.median()),
            "max_age_days":    int(ages.max()),
            "stale_records":   int(len(parsed) - fresh),
            "total_dated":     len(parsed),
        }
        scores.append(score)

    overall = round(np.mean(scores), 2) if scores else 100.0
    return {"score": overall, "column_detail": results}


# ===================================================================================================
#  Dimension 6: Accuracy (statistical outlier detection)
# ===================================================================================================
def check_accuracy(df: pd.DataFrame, schema: dict) -> dict:
    results = {}
    scores = []
    num_cols = [c for c, r in schema["columns"].items() if r.get(
        "type") == "numeric" and c in df.columns]

    for col in num_cols:
        series = pd.to_numeric(df[col], errors="coerce").dropna()

        if len(series) < 10:
            continue

        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        lo, hi = q1 - 3 * iqr, q3 + 3 * iqr
        outliers = series[(series < lo) | (series > hi)]
        score = _score(len(series) - len(outliers), len(series))
        results[col] = {
            "score":          score,
            "outlier_count":  int(len(outliers)),
            "total":          int(len(series)),
            "lower_fence":    round(float(lo), 2),
            "upper_fence":    round(float(hi), 2),
            "outlier_values": [round(float(v), 2) for v in outliers.head(5).tolist()],
        }
        scores.append(score)

    overall = round(np.mean(scores), 2) if scores else 100.0
    return {"score": overall, "column_detail": results}
