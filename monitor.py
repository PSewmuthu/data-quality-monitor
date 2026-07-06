'''
monitor.py - Data Quality Monitoring System
Entry point. Load datasets, run checks, fires alerts, saves reports, and refreshes the HTML dashboard with live data.

Usage:
    python monitor.py                            # uses existing sample data
    python monitor.py --generate                 # regenerate sample data first
    python monitor.py --data path/to/csvs/       # custom CSV folder
    python monitor.py --output path/to/reports/  # custom output folder
    python monitor.py --max-age 180              # timeliness window (days)
'''
import os
import sys
import logging
import argparse
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__)) if os.path.dirname(
    __file__) not in sys.path else None

from core import (
    run_checks, generate_alerts, print_alerts,
    save_json_report, save_csv_summary, save_alerts_csv,
    print_console_report, update_dashboard
)

logging.basicConfig(level=logging.INFO)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')

DATASET_FILES = {
    "candidates": "candidates.csv",
    "job_postings": "job_postings.csv",
    "applications": "applications.csv"
}


def load_datasets(data_dir: str) -> dict:
    datasets = {}

    for name, fname in DATASET_FILES.items():
        path = os.path.join(data_dir, fname)
        if os.path.exists(path):
            datasets[name] = pd.read_csv(path)
            logging.info(
                f"[Loader] Loaded '{name}': {len(datasets[name])} rows from {path}")
        else:
            logging.warning(
                f"[Loader] Dataset file '{fname}' not found in {data_dir}. Skipping.")

    return datasets


def run_pipeline(data_dir: str, max_age: int, output_dir: str = "output/reports"):
    # ------------ Load datasets ------------
    logging.info("[Pipeline] Loading datasets...")
    datasets = load_datasets(data_dir)

    if not datasets:
        logging.error("[Pipeline] No datasets loaded. Exiting...")
        sys.exit(1)

    # ------------ Data Quality Checks ------------
    logging.info("[Pipeline] Running data quality checks...")
    results = run_checks(datasets, max_age_days=max_age)

    # ------------ Generate alerts ------------
    logging.info("[Pipeline] Evaluating alert rules...")
    alerts = generate_alerts(results)
    print_alerts(alerts)

    # ------------ Console report ------------
    print_console_report(results, alerts)

    # ------------ Save time-stamped reports ------------
    logging.info("[Pipeline] Saving reports...")
    os.makedirs(output_dir, exist_ok=True)

    save_json_report(results, alerts, output_dir)
    save_csv_summary(results, alerts, output_dir)
    save_alerts_csv(alerts, output_dir)

    # ------------ Refresh HTML dashboard with live data ------------
    logging.info("[Pipeline] Refreshing HTML dashboard...")
    update_dashboard(results, alerts, output_dir)

    logging.info(
        "[Pipeline] Data Quality Monitoring pipeline completed successfully.")
    print(
        f"\nSystem Score: {results['system_score']:.1f} [{results['system_status']}]")
    print(f"   Open output/dq_dashboard.html in a browser to view the dashboard.\n")

    return results, alerts


def generate_sample_data():
    logging.info("[Data Generation] Generating sample datasets...")
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "gen", os.path.join(DATA_DIR, "generate_sample_data.py")
    )
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)

    gen.generate_candidates(300).to_csv(
        os.path.join(DATA_DIR, "candidates.csv"), index=False)
    gen.generate_jobs(80).to_csv(os.path.join(
        DATA_DIR, "job_postings.csv"), index=False)

    cdf = pd.read_csv(os.path.join(DATA_DIR, "candidates.csv"))
    jdf = pd.read_csv(os.path.join(DATA_DIR, "job_postings.csv"))

    gen.generate_applications(cdf, jdf, 500).to_csv(
        os.path.join(DATA_DIR, "applications.csv"), index=False)

    logging.info("[Data Generation] Sample datasets generated successfully.")


def main():
    parser = argparse.ArgumentParser(
        description="Data Quality Monitoring System")
    parser.add_argument(
        "--data", type=str, default=DATA_DIR,
        help="Directory containing the datasets (default: 'data/').")
    parser.add_argument(
        "--output", type=str, default=OUTPUT_DIR / "reports",
        help="Directory to save reports (default: 'output/reports').")
    parser.add_argument(
        "--generate", action="store_true",
        help="Regenerate sample data before running.")
    parser.add_argument(
        "--max_age", type=int, default=365,
        help="Timeliness max-age threshold in days (default: 365).")
    args = parser.parse_args()

    print("\n┌────────────────────────────────────────────────────────────────────┐")
    print("│                 DATA QUALITY MONITORING SYSTEM                     │")
    print("└────────────────────────────────────────────────────────────────────┘\n")

    if args.generate:
        generate_sample_data()

    results, alerts = run_pipeline(args.data, args.max_age, args.output)

    return results, alerts


if __name__ == "__main__":
    main()
