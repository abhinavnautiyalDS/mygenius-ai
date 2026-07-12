import sqlite3
import pandas as pd

DB_PATH = "data/sqlite/finance.db"

conn = sqlite3.connect(DB_PATH)

clients = pd.read_csv(
    "data/datasets/clients.csv"
)

investments = pd.read_csv(
    "data/datasets/investments.csv"
)

clients.to_sql(
    "clients",
    conn,
    if_exists="replace",
    index=False
)

investments.to_sql(
    "investments",
    conn,
    if_exists="replace",
    index=False
)

conn.close()

print("Database created successfully.")
