"""Local CSV ETL pipeline with optional Snowflake loading."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "sample_data" / "sales_raw.csv"
OUTPUT_DIR = ROOT / "output"
CLEAN_FILE = OUTPUT_DIR / "sales_clean.csv"
REPORT_FILE = OUTPUT_DIR / "quality_report.json"

REQUIRED_COLUMNS = [
    "order_id", "order_date", "customer_id", "customer_name",
    "product", "quantity", "unit_price", "region",
]


def clean_sales_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Normalize, validate and clean sales rows; return clean data and report."""
    input_rows = int(len(df))
    df = df.copy()
    df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]

    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Input CSV is missing required columns: {missing_columns}")

    # Trim whitespace in text columns and standardize empty strings to null.
    for col in ["order_id", "customer_id", "customer_name", "product", "region"]:
        df[col] = df[col].astype("string").str.strip()
        df[col] = df[col].replace("", pd.NA)

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")

    # Remove duplicate order IDs, keeping the first record.
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["order_id"], keep="first")
    duplicate_rows_removed = int(before_dedup - len(df))

    # Invalid rows are excluded from the clean output and counted in the report.
    valid_mask = (
        df["order_id"].notna()
        & df["order_date"].notna()
        & df["customer_id"].notna()
        & df["customer_name"].notna()
        & df["product"].notna()
        & df["region"].notna()
        & df["quantity"].notna()
        & df["unit_price"].notna()
        & (df["quantity"] > 0)
        & (df["unit_price"] >= 0)
    )
    invalid_rows_removed = int((~valid_mask).sum())
    clean = df.loc[valid_mask].copy()

    clean["order_date"] = clean["order_date"].dt.strftime("%Y-%m-%d")
    clean["quantity"] = clean["quantity"].astype("int64")
    clean["unit_price"] = clean["unit_price"].astype(float)
    clean["total_amount"] = clean["quantity"] * clean["unit_price"]

    # Reorder columns for consistent downstream loading.
    clean = clean[
        ["order_id", "order_date", "customer_id", "customer_name",
         "product", "quantity", "unit_price", "total_amount", "region"]
    ].sort_values("order_id").reset_index(drop=True)

    report = {
        "input_file": str(INPUT_FILE.relative_to(ROOT)),
        "input_rows": input_rows,
        "duplicate_rows_removed": duplicate_rows_removed,
        "invalid_rows_removed": invalid_rows_removed,
        "output_rows": int(len(clean)),
        "output_columns": list(clean.columns),
        "null_counts_after_cleaning": {
            col: int(clean[col].isna().sum()) for col in clean.columns
        },
        "checks": {
            "order_id_unique": bool(clean["order_id"].is_unique),
            "required_values_present": bool(clean[REQUIRED_COLUMNS].notna().all().all())
                if all(c in clean.columns for c in REQUIRED_COLUMNS) else True,
            "quantity_positive": bool((clean["quantity"] > 0).all()),
            "unit_price_non_negative": bool((clean["unit_price"] >= 0).all()),
        },
    }
    return clean, report


def load_to_snowflake(df: pd.DataFrame) -> int:
    """Insert clean rows into a pre-created Snowflake table."""
    load_dotenv(ROOT / ".env")
    required_env = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD"]
    missing = [key for key in required_env if not os.getenv(key)]
    if missing:
        raise RuntimeError(
            f"Missing environment values {missing}. Copy .env.example to .env "
            "and fill in your own Snowflake credentials."
        )

    import snowflake.connector

    conn_args = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "password": os.environ["SNOWFLAKE_PASSWORD"],
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "DATA_ENGINEERING_WH"),
        "database": os.getenv("SNOWFLAKE_DATABASE", "DATA_ENGINEERING_DB"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
    }
    if os.getenv("SNOWFLAKE_ROLE"):
        conn_args["role"] = os.environ["SNOWFLAKE_ROLE"]

    conn = snowflake.connector.connect(**conn_args)
    try:
        table = os.getenv("SNOWFLAKE_TABLE", "SALES_RAW")
        # Table name is configurable but restricted to safe SQL identifier characters.
        if not table.replace("_", "").isalnum():
            raise ValueError("SNOWFLAKE_TABLE must contain only letters, numbers, underscores.")
        insert_sql = f"""
            INSERT INTO {table}
            (ORDER_ID, ORDER_DATE, CUSTOMER_ID, CUSTOMER_NAME, PRODUCT,
             QUANTITY, UNIT_PRICE, TOTAL_AMOUNT, REGION)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        rows = [
            (
                str(row.order_id), str(row.order_date), str(row.customer_id),
                str(row.customer_name), str(row.product), int(row.quantity),
                float(row.unit_price), float(row.total_amount), str(row.region)
            )
            for row in df.itertuples(index=False)
        ]
        if rows:
            with conn.cursor() as cur:
                cur.executemany(insert_sql, rows)
        return len(rows)
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean CSV sales data and optionally load to Snowflake.")
    parser.add_argument(
        "--load-snowflake", action="store_true",
        help="Insert cleaned rows into the configured Snowflake table."
    )
    args = parser.parse_args()

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input CSV not found: {INPUT_FILE}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(INPUT_FILE)
    clean, report = clean_sales_data(raw)
    clean.to_csv(CLEAN_FILE, index=False)
    REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("ETL completed.")
    print(f"Input rows:             {report['input_rows']}")
    print(f"Duplicate rows removed: {report['duplicate_rows_removed']}")
    print(f"Invalid rows removed:   {report['invalid_rows_removed']}")
    print(f"Clean output rows:      {report['output_rows']}")
    print(f"Clean CSV:              {CLEAN_FILE}")
    print(f"Quality report:         {REPORT_FILE}")

    if args.load_snowflake:
        inserted = load_to_snowflake(clean)
        print(f"Rows inserted into Snowflake: {inserted}")


if __name__ == "__main__":
    main()
