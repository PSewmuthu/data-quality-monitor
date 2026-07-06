'''
dashboard_builder.py - Regenerates dq_dashboard.html with live DQ_DATA.
Called automatically by monitor.py after every run.
'''
import os
import re
import json
from typing import List, Dict

_TEMPLATE_PATH = os.path.join(os.path.dirname(
    __file__), "..", "output", "dq_dashboard.html")


def _build_dq_data(results: dict, alerts: List[Dict]) -> dict:
    '''Flatten results + alerts into the shape the dashboard JS expects'''

    datasets_out = {}
    for ds_name, ds in results["datasets"].items():
        dims_out = {}
        for dim, data in ds["dimensions"].items():
            dims_out[dim] = {
                "score":  round(data.get("score", 0), 2),
                "status": data.get("status", "UNKNOWN"),
            }
        datasets_out[ds_name] = {
            "overall_score":  ds["overall_score"],
            "overall_status": ds["overall_status"],
            "row_count":      ds["row_count"],
            "col_count":      ds.get("col_count", 0),
            "dimensions":     dims_out,
        }

    alerts_out = [
        {
            "id":        a["id"],
            "timestamp": a["timestamp"],
            "severity":  a["severity"],
            "dataset":   a["dataset"],
            "rule":      a["rule"],
            "message":   a["message"],
            "score":     round(a.get("score", 0), 2),
            "dimension": a.get("dimension", ""),
        }
        for a in alerts
    ]

    return {
        "system_score": results["system_score"],
        "system_status": results["system_status"],
        "run_time": results["run_time"],
        "datasets": datasets_out,
        "alerts": alerts_out,
    }


def update_dashboard(results: dict, alerts: List[Dict], output_dir: str) -> str:
    '''
    Reads the existing dashboard HTML, replaces the DQ_DATA block with fresh
    data, and writes the updated file to output_dir/dq_dashboard.html.
    Returns the output path.
    '''

    tpl_path = os.path.join(output_dir, "dq_dashboard.html")
    if not os.path.exists(tpl_path):
        print(
            f"  ⚠️  Dashboard template not found at {tpl_path} — skipping update")
        return tpl_path

    with open(tpl_path, "r", encoding="utf-8") as f:
        html = f.read()

    dq_data = _build_dq_data(results, alerts)
    new_block = "const DQ_DATA = " + json.dumps(dq_data, indent=2) + ";"

    # Replace everything between "const DQ_DATA = {" ... "};"
    pattern = r"const DQ_DATA = \{.*?\};"
    updated = re.sub(pattern, new_block, html, flags=re.DOTALL)

    if updated == html:
        print("  ⚠️  DQ_DATA block not found in dashboard HTML — data not injected")
    else:
        with open(tpl_path, "w", encoding="utf-8") as f:
            f.write(updated)
        print(f"  🖥️  Dashboard updated → {tpl_path}")

    return tpl_path
