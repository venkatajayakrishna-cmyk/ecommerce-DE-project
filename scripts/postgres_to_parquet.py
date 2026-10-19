import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import URL


# 1. Find the project root and load configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

PARQUET_DIR = PROJECT_ROOT / "data" / "processed" / "parquet"


# 2. Read PostgreSQL connection settings
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

if not all([db_host, db_port, db_name, db_user, db_password]):
    raise ValueError("Missing database settings in .env")


# 3. Create the database connection engine
connection_url = URL.create(
    drivername="postgresql+psycopg",
    username=db_user,
    password=db_password,
    host=db_host,
    port=int(db_port),
    database=db_name,
)

engine = create_engine(connection_url)


try:
    # 4. Discover the tables in the raw schema
    inspector = inspect(engine)
    table_names = sorted(
        inspector.get_table_names(schema="raw")
    )

    if not table_names:
        raise RuntimeError(
            "No tables found in the PostgreSQL raw schema."
        )

    # 5. Create the destination directory
    PARQUET_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Found {len(table_names)} tables in raw.")

    # 6. Export each table to a Parquet file
    for table_name in table_names:
        print(f"\nExporting table: {table_name}")

        df = pd.read_sql_table(
            table_name,
            con=engine,
            schema="raw",
        )

        output_path = PARQUET_DIR / f"{table_name}.parquet"

        df.to_parquet(
            output_path,
            engine="pyarrow",
            index=False,
            compression="snappy",
        )

        # 7. Read the exported file back and verify its row count
        exported_df = pd.read_parquet(
            output_path,
            engine="pyarrow",
        )

        source_rows = len(df)
        exported_rows = len(exported_df)

        print(f"PostgreSQL rows: {source_rows}")
        print(f"Parquet rows: {exported_rows}")
        print(f"File: {output_path}")

        if source_rows != exported_rows:
            raise RuntimeError(
                f"Row count mismatch for {table_name}"
            )

    print("\nAll tables exported and row counts verified.")

finally:
    # 8. Release database connection resources
    engine.dispose()