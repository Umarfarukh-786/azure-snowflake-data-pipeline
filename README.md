# Azure-to-Snowflake Data Pipeline (Beginner Portfolio Project)

A beginner-friendly data engineering portfolio project that demonstrates:
- CSV ingestion
- Python/Pandas cleaning and transformation
- Data-quality checks and a JSON quality report
- Optional loading into Snowflake
- Snowflake SQL for staging and analytics
- A practical guide for extending the pipeline with Azure Data Factory (ADF) and ADLS Gen2

> **Important:** The local pipeline runs without Azure or Snowflake accounts. The Azure and Snowflake sections are learning/deployment instructions, not claims that a cloud deployment has already happened. Do not describe the cloud integration as completed on your resume until you configure and test it yourself.

## Architecture

```text
sample_data/sales_raw.csv
        |
        v
Python + Pandas ETL
  - normalize column names
  - parse dates and numeric values
  - remove duplicate order IDs
  - check required fields and invalid values
        |
        +----> output/sales_clean.csv
        |
        +----> output/quality_report.json
        |
        +----> optional Snowflake table load
```

Cloud extension to build:
```text
CSV in ADLS Gen2 -> Azure Data Factory -> Snowflake landing table
                                             |
                                             v
                                      SQL transformations
                                             |
                                             v
                                      analytics tables
```

## 1. Requirements

- Python 3.10 or newer
- Optional: a Snowflake account and credentials for the Snowflake loading step
- Optional: an Azure subscription for the cloud extension

## 2. Run locally

### Windows (PowerShell / CMD)

```bash
python -m venv .venv
```

Activate the environment:

PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```

CMD:
```bat
.venv\Scripts\activate
```

Install packages:
```bash
pip install -r requirements.txt
```

Run the ETL:
```bash
python src/etl_pipeline.py
```

Expected output:
- `output/sales_clean.csv`
- `output/quality_report.json`

The script prints a summary including input rows, output rows, duplicate rows removed, invalid rows removed, and null counts.

## 3. Optional: Load cleaned data into Snowflake

1. Create a Snowflake database/schema/table using `sql/01_setup.sql`.
2. Copy `.env.example` to `.env` and fill in your own Snowflake account details.
3. Install requirements (the Snowflake connector is listed in `requirements.txt`).
4. Run:
   ```bash
   python src/etl_pipeline.py --load-snowflake
   ```
5. Verify the table using the queries in `sql/02_analytics.sql`.

Never commit `.env`, passwords, private keys, or account credentials to GitHub.

The Snowflake loader uses the Snowflake Python connector and inserts cleaned rows into `SALES_RAW`. For a small learning dataset this is fine; for large production datasets, use bulk loading (for example, staged files and `COPY INTO`) rather than row-by-row inserts.

## 4. Snowflake SQL

- `sql/01_setup.sql`: creates a database, schema, warehouse, and landing table.
- `sql/02_analytics.sql`: example analytical transformations and quality queries.

Run the setup script in a Snowflake worksheet. Confirm that your role is allowed to create these objects and that warehouse usage is permitted. A warehouse can incur cost while running; suspend it when finished.

## 5. Azure Data Factory + ADLS Gen2 extension

Use this as the cloud implementation checklist:

1. Create an Azure Storage account with hierarchical namespace enabled (ADLS Gen2).
2. Create a container such as `landing` and upload `sample_data/sales_raw.csv`.
3. In Azure Data Factory, create linked services for ADLS Gen2 and Snowflake. Use secure authentication supported by your tenant/account; do not put passwords in source files.
4. Create an ADLS Gen2 delimited-text dataset pointing to the CSV.
5. Create a Snowflake dataset pointing to the `DATA_ENGINEERING_DB.PUBLIC.SALES_RAW` table.
6. Add a Copy Data activity: ADLS Gen2 dataset as source, Snowflake dataset as sink. Map the source columns to the destination columns.
7. Debug the pipeline and inspect the run output. Verify row counts in Snowflake.
8. Add a second activity or separate SQL step for transformations and quality checks.
9. Capture screenshots of the successful ADF run and Snowflake query results for your portfolio.
10. Delete or pause cloud resources when not in use to avoid unnecessary charges.

ADF connector screens and supported authentication choices can change. Follow the connector documentation shown in your Azure portal and use the current Microsoft/Snowflake connector setup instructions.

## 6. Suggested GitHub README evidence

After you have personally run each step, add:
- Screenshot of local ETL summary
- A sample `quality_report.json`
- Screenshot of Snowflake table and analytics query results (only if you really loaded it)
- Screenshot of a successful ADF run (only after deploying it)
- Short notes on issues encountered and how you resolved them

## 7. Resume bullets (use only what you have actually completed)

**After local version only:**
- Built a Python/Pandas ETL pipeline to ingest CSV sales data, normalize fields, validate required values, remove duplicate order IDs, and generate a data-quality report.
- Wrote Snowflake SQL for landing-table setup and analytical transformations; practised data quality checks and aggregation queries.

**Only after successful cloud implementation:**
- Orchestrated CSV ingestion from ADLS Gen2 to Snowflake using Azure Data Factory and validated row counts and data quality.
- Transformed landing data in Snowflake SQL to produce analytics-ready sales summaries.

## 8. Project limitations / next steps

This is a portfolio starter project, not a production-ready enterprise pipeline. Next improvements could include incremental loads, logging, retries, schema-drift handling, orchestration schedules, automated tests, and role-based access controls.
