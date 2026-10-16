import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from etl_pipeline import clean_sales_data


def test_cleaning_removes_duplicate_and_invalid_rows():
    raw = pd.DataFrame([
        {"order_id":"1","order_date":"2026-01-01","customer_id":"C1","customer_name":"A",
         "product":"P","quantity":2,"unit_price":10,"region":"North"},
        {"order_id":"1","order_date":"2026-01-01","customer_id":"C1","customer_name":"A",
         "product":"P","quantity":2,"unit_price":10,"region":"North"},
        {"order_id":"2","order_date":"bad-date","customer_id":"C2","customer_name":"B",
         "product":"Q","quantity":1,"unit_price":5,"region":"South"},
    ])
    clean, report = clean_sales_data(raw)
    assert len(clean) == 1
    assert report["duplicate_rows_removed"] == 1
    assert report["invalid_rows_removed"] == 1
    assert clean.iloc[0]["total_amount"] == 20
