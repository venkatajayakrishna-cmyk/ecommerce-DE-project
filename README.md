# E-commerce Data Engineering Project

## Objective
Build an end-to-end data pipeline using
PostgreSQL, Python, Apache Airflow, Databricks,
dbt Core and Power BI.

## Current Stage
Initial batch ingestion from Kaggle CSV files
into PostgreSQL.

## Current Architecture
Kaggle CSV files
    -> Python/Pandas
    -> PostgreSQL raw schema

## Next Steps
1. Validate the PostgreSQL tables.
2. Extract data into Parquet files.
3. Upload files to Databricks.
4. Ingest data into Delta tables.
5. Transform data using dbt Core.
6. Orchestrate the pipeline with Airflow.
7. Create a Power BI dashboard.