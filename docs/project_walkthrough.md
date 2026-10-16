# Project walkthrough for interview preparation

## What does the project do?
It reads sales rows from a CSV file, cleans and validates them with Pandas, calculates a total amount for each order, writes a clean CSV, and generates a JSON report. An optional loader inserts the clean rows into a Snowflake table.

## What is ETL?
Extract: read the CSV.
Transform: normalize column names, parse dates/numbers, remove duplicate order IDs, reject invalid rows, and calculate `total_amount`.
Load: save the cleaned file and optionally insert it into Snowflake.

## Why create a quality report?
It gives evidence about how many rows came in, how many duplicate and invalid rows were removed, how many rows remain, and whether basic rules passed.

## What is a virtual warehouse in Snowflake?
It is compute used to execute queries and data-loading operations. It is separate from the database's stored data. Warehouse size and runtime can affect cost.

## What does Azure Data Factory do?
ADF is a cloud data integration/orchestration service. In this project's cloud extension, it can move data from ADLS Gen2 into Snowflake and report pipeline activity status.

## What is ADLS Gen2?
Azure Data Lake Storage Gen2 is Azure object storage with hierarchical namespace capabilities, often used to hold raw and processed analytical files.

## What is the limitation of the starter project?
The Python ETL runs locally. Snowflake loading is optional and requires credentials and a created table. Azure Data Factory is a guided extension that must be configured and run separately in an Azure account.
