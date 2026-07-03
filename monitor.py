'''
monitor.py - Data Quality Monitoring System
Entry point. Load datasets, run checks, fires alerts, saves reports, and refreshes the HTML dashboard with live data.
'''
import os
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')

os.makedirs(OUTPUT_DIR, exist_ok=True)

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
