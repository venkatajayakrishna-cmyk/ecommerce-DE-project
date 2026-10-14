import os
import re
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

RAW_DIR = PROJECT_ROOT / "data" / "raw"

db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

if not all([db_host, db_port, db_name, db_user, db_password]):
    raise ValueError("Missing database settings in .env")

connection_url = URL.create(
    drivername="postgresql+psycopg",
    username=db_user,
    password=db_password,
    host=db_host,
    port=int(db_port),
    database=db_name,
)

engine = create_engine(connection_url)

with engine.connect() as connection:
    version = connection.execute(
        text("SELECT version()")
    ).scalar_one()

with engine.begin() as connection:
    connection.execute(
        text("CREATE SCHEMA IF NOT EXISTS raw")
    )

csv_files = sorted(RAW_DIR.glob("*.csv"))

if not csv_files:
    raise FileNotFoundError(f"No CSV files found in {RAW_DIR}")

for csv_file in csv_files:
    table_name = re.sub(
        r"[^a-zA-Z0-9_]",
        "_",
        csv_file.stem.lower()
    )

    print(f"\nReading {csv_file.name}")

    df = pd.read_csv(
        csv_file,
        low_memory=False,
    )

    print("Rows in source file:", len(df))
    print("Columns:", list(df.columns))

    df.to_sql(
        name=table_name,
        con=engine,
        schema='raw',
        if_exists='replace',
        index=False,
        chunksize=1000,
    )

print("Ingestion Complete")

engine.dispose()