"""Run the packaged SQL against synthetic tables in an in-memory SQLite database."""
from pathlib import Path
import sqlite3
import pandas as pd


def run_sql(raw: pd.DataFrame,events: pd.DataFrame,sql_path: Path) -> pd.DataFrame:
    with sqlite3.connect(":memory:") as con:
        raw.to_sql("surveys",con,index=False)
        events.to_sql("events",con,index=False)
        return pd.read_sql_query(sql_path.read_text(encoding="utf-8"),con)
