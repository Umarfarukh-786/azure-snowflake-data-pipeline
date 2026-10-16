# Azure Data Factory implementation checklist

This checklist is intentionally not a claim of a deployed Azure environment. Use it when you build the cloud extension in your own subscription.

## Prerequisites
- Azure subscription
- Storage account with hierarchical namespace enabled (ADLS Gen2)
- Azure Data Factory instance
- Snowflake account with the target table created using `sql/01_setup.sql`

## Steps
1. Create an ADLS Gen2 container, for example `landing`.
2. Upload `sample_data/sales_raw.csv` to the container.
3. In Azure Data Factory, create a linked service for ADLS Gen2 using an approved authentication method.
4. Create a linked service for Snowflake using the connector/authentication method available in your environment.
5. Create a delimited-text source dataset that points to the uploaded CSV.
6. Create a Snowflake sink dataset for `DATA_ENGINEERING_DB.PUBLIC.SALES_RAW`.
7. Add a Copy Data activity. Select the ADLS dataset as the source and Snowflake as the sink.
8. Import/map the columns. Ensure the destination schema matches the CSV-to-clean-data design, or use the cleaned CSV produced by the local Python ETL.
9. Debug the pipeline and review the activity output. Check source/sink row counts.
10. Run `sql/02_analytics.sql` and compare results with expected data.
11. Add a pipeline schedule only after the manual run works.
12. Capture real screenshots of the successful pipeline run and Snowflake query output.

## Notes
- The local Python script removes duplicate order IDs and invalid rows. If you copy the raw CSV directly through ADF, those same quality rules are not automatically applied. For a consistent result, upload `output/sales_clean.csv` or add transformations/validation in the cloud workflow.
- Keep secrets in secure linked-service configuration or a supported secret store, never in Git.
- Stop/suspend resources when not in use. Verify current pricing before creating paid resources.
