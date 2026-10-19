# End-to-End Data Engineering Project

An end-to-end data engineering portfolio project that starts with a Kaggle dataset and progressively builds a pipeline using PostgreSQL, Python, Parquet, Databricks, dbt Core, Apache Airflow, and Power BI.

> **Current scope:** This README documents the project through the PostgreSQL ingestion and PostgreSQL-to-Parquet export stages. The Databricks, dbt Core, Airflow, and Power BI stages are planned and have not yet been documented as implemented.

## Project Objectives

- Load the source CSV files into PostgreSQL in a repeatable way.
- Keep the original source files separate from generated outputs.
- Export PostgreSQL tables to Parquet for efficient analytical processing and transfer.
- Validate that the data was loaded and exported as expected.
- Extend the pipeline in later stages to Databricks Delta tables, dbt models, Airflow orchestration, and Power BI dashboards.

## Current Architecture

```text
Kaggle ZIP download
        |
        v
Extracted CSV files
        |
        v
Python + Pandas
        |
        v
PostgreSQL database: ecommerce_db
Schema: raw
        |
        v
Python + Pandas + PyArrow
        |
        v
data/processed/parquet/*.parquet
```

The database name `ecommerce_db` is the name used in the current setup instructions. The source dataset's exact Kaggle title and URL can be added below once confirmed.

## Technologies Used So Far

| Technology | Role in this project |
|---|---|
| Python | Runs the ingestion and export scripts. |
| `uv` | Manages project dependencies, the virtual environment, and the lockfile. |
| Pandas | Reads CSV files into DataFrames, reads SQL tables, and writes tabular outputs. |
| SQLAlchemy | Provides the database engine and SQL interface used by Pandas. |
| Psycopg | PostgreSQL database driver used by SQLAlchemy. |
| `python-dotenv` | Loads database connection configuration from `.env`. |
| PostgreSQL | Stores the imported source tables in the `raw` schema. |
| PyArrow | Provides the Parquet read/write engine used by Pandas. |
| Parquet | Column-oriented, typed file format used for exported data. |

## Project Structure

```text
Complete_DE_Project/
├── .env                              # Local database settings; never commit
├── .gitignore                        # Excludes secrets, environments, and data files
├── pyproject.toml                    # Project configuration and dependencies
├── uv.lock                           # Resolved dependency versions
├── README.md
├── data/
│   ├── raw/                          # Extracted source CSV files
│   └── processed/
│       └── parquet/                  # Parquet files exported from PostgreSQL
└── scripts/
    ├── ingest_to_postgres.py         # CSV-to-PostgreSQL ingestion
    └── export_postgres_to_parquet.py # PostgreSQL-to-Parquet export
```

The `data` directories are local working directories and are excluded from Git. Source files can be downloaded again from the original dataset source when needed.

## Prerequisites

- Python installed and available from the terminal.
- `uv` installed and available from the terminal.
- PostgreSQL server running locally.
- pgAdmin or another PostgreSQL client for database setup and verification.
- The Kaggle ZIP downloaded and extracted.

## Initial Setup

### 1. Place the source CSV files

Copy the extracted `.csv` files directly into `data/raw/`.

The current ingestion script searches for CSV files directly inside this folder; it does not recursively search nested subdirectories.

### 2. Initialize the Python project

From the project root, initialize the project if `pyproject.toml` does not already exist:

```powershell
uv init --bare
```

If the project has already been initialized, do not initialize it again.

### 3. Install dependencies

```powershell
uv add pandas sqlalchemy "psycopg[binary]" python-dotenv pyarrow
```

This records dependencies in `pyproject.toml`, updates `uv.lock`, and synchronizes the project environment. If dependencies are already declared, use `uv sync` to synchronize the environment with the project configuration.

### 4. Create the PostgreSQL database

In pgAdmin, create a database named `ecommerce_db` if it does not already exist.

Open the Query Tool for `ecommerce_db` and create the schema:

```sql
CREATE SCHEMA IF NOT EXISTS raw;
```

The `raw` schema stores the source tables imported from the CSV files.

### 5. Configure the local database connection

Create a `.env` file in the project root:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ecommerce_db
DB_USER=postgres
DB_PASSWORD="YOUR_ACTUAL_POSTGRES_PASSWORD"
```

Replace the placeholder with the password for your local PostgreSQL user. Do not commit `.env` or share the password.

### 6. Verify Git exclusions

The `.gitignore` should include at least:

```gitignore
.env
.venv/
__pycache__/
*.pyc
data/raw/
data/processed/
```

This keeps credentials, local Python environment files, caches, and data files out of Git commits.

## Stage 1 — CSV Files to PostgreSQL

**Script:** `scripts/ingest_to_postgres.py`

### What it does

1. Finds the project root and loads `.env`.
2. Validates that the required PostgreSQL connection settings are present.
3. Finds `.csv` files directly inside `data/raw/`.
4. Connects to PostgreSQL using SQLAlchemy and Psycopg.
5. Ensures the `raw` schema exists.
6. Reads each CSV into a Pandas DataFrame.
7. Writes each DataFrame to a table in `ecommerce_db.raw`.
8. Queries PostgreSQL for the destination row count and compares it with the source DataFrame row count.
9. Releases SQLAlchemy engine resources.

### Run the ingestion script

From the project root:

```powershell
uv run python .\scripts\ingest_to_postgres.py
```

The script prints the source file name, source row count, column names, destination table, and destination row count.

### Table naming

The script derives PostgreSQL table names from CSV filenames. It removes the `.csv` extension, converts the name to lowercase, and replaces unsupported characters with underscores.

For example, `Orders Dataset.csv` would become `orders_dataset`.

### Important behavior

The script currently uses:

```python
df.to_sql(
    name=table_name,
    con=engine,
    schema="raw",
    if_exists="replace",
    index=False,
    chunksize=1000,
)
```

`if_exists="replace"` drops and recreates a destination table when it already exists. This is convenient for an initial development load, but it is destructive to any changes made directly to the table and does not preserve table-level constraints or indexes. It should be reconsidered before using the pipeline for recurring or production ingestion.

Pandas also infers database column types. The current script does not define a complete relational schema with primary keys, foreign keys, or business constraints.

## Stage 2 — PostgreSQL Tables to Parquet

**Script:** `scripts/export_postgres_to_parquet.py`

### What it does

1. Loads the same PostgreSQL connection configuration from `.env`.
2. Uses SQLAlchemy inspection to discover tables in the `raw` schema.
3. Creates `data/processed/parquet/` if it does not exist.
4. Reads each table from PostgreSQL into a Pandas DataFrame.
5. Writes each table to a `.parquet` file using PyArrow and Snappy compression.
6. Reads each generated Parquet file back and compares its row count to the DataFrame row count.
7. Releases database connection resources.

### Run the export script

First ensure that Stage 1 has successfully populated PostgreSQL. Then run:

```powershell
uv run python .\scripts\export_postgres_to_parquet.py
```

The generated files are written to:

```text
data/processed/parquet/
```

Each table is exported as a same-named Parquet file; for example, a table named `orders` is written to `orders.parquet`.

### Why Parquet?

Parquet is a binary, column-oriented file format designed for efficient analytical data processing. It supports typed columns and compression and can allow analytical engines to read only the columns required by a query. It is a file format, not a database or a table-management system.

The current export uses Snappy compression:

```python
df.to_parquet(
    output_path,
    engine="pyarrow",
    index=False,
    compression="snappy",
)
```

`index=False` avoids exporting the Pandas row index as an extra data column.

### Current limitations

- The script reads each complete PostgreSQL table into memory before exporting it. Very large tables may require chunked extraction or a bulk-export approach.
- Matching row counts verifies that the number of rows is consistent, but does not prove that every column value is identical. More validation can be added for schemas, keys, nulls, and column values.
- Rerunning the script overwrites each generated Parquet file with a fresh export.
- The export discovers tables in the `raw` schema, so only tables in that schema are included.

## Data Verification

### List tables in the `raw` schema

Run in the Query Tool for `ecommerce_db`:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'raw'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;
```

### Inspect a table

Replace `your_table_name` with a table name returned by the previous query:

```sql
SELECT *
FROM raw.your_table_name
LIMIT 10;
```

### Count rows

```sql
SELECT COUNT(*)
FROM raw.your_table_name;
```

Compare this count with the source and destination counts printed by the ingestion script. The export script also compares the DataFrame row count with the Parquet row count after reading the file back.

## Security and Data Handling

- Keep database credentials in `.env`, not in Python source code.
- Do not commit `.env` to GitHub.
- Keep `.venv/`, `data/raw/`, and `data/processed/` out of Git.
- Document the dataset source so reviewers can obtain the data independently.
- Do not expose a local PostgreSQL server publicly to make it available to a cloud service. Future cloud connectivity must be designed with appropriate network access and credentials.

## Implementation Status

| Stage | Scope | Status |
|---|---|---|
| 1 | Kaggle CSV files → PostgreSQL `raw` schema | Script and validation logic prepared; run and verify locally. |
| 2 | PostgreSQL `raw` tables → Parquet files | Script and row-count validation logic prepared; run and verify locally. |
| 3 | Upload Parquet files to Databricks | Planned |
| 4 | Ingest files into Bronze Delta tables | Planned |
| 5 | Transform and test data using dbt Core | Planned |
| 6 | Orchestrate pipeline with Apache Airflow | Planned |
| 7 | Build Power BI dashboard from modeled data | Planned |

> Update the status table after each stage has been run and verified successfully. Writing a script is not the same as confirming that it works in the local environment.

## Planned End-State Architecture

```text
Kaggle CSV files
      |
      v
Python / Pandas
      |
      v
PostgreSQL raw schema
      |
      v
Python extraction to Parquet
      |
      v
Databricks file storage / ingestion
      |
      v
Bronze Delta tables
      |
      v
Silver and Gold models using dbt Core
      |
      v
Power BI dashboard

Apache Airflow will orchestrate the appropriate pipeline tasks.
```

The future Databricks storage and transfer method will be selected after checking the available Databricks environment and its networking/storage capabilities. Airflow is planned to schedule and manage task dependencies, retries, and execution; it is not a replacement for the transformations performed by dbt or the compute provided by Databricks.

## Next Steps

1. Run the CSV-to-PostgreSQL ingestion script and confirm the source and destination row counts match.
2. Run the PostgreSQL-to-Parquet export script and confirm the output files are readable and row counts match.
3. Record the actual Kaggle dataset title, source URL, and tables included.
4. Choose and verify the available Databricks environment and a suitable secure way to transfer files.
5. Ingest the Parquet files into Bronze Delta tables.
6. Add dbt Core models and data quality tests.
7. Orchestrate the workflow using Apache Airflow.
8. Build a Power BI dashboard from the modeled data.
