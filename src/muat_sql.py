from pathlib import Path
import duckdb
import pandas as pd

DB_PATH = "data/db/capstone.duckdb"
SKEMA = "sql/schema.sql"

# tabel SQL -> berkas sumber (Parquet atau CSV)
TABEL = {
    "silver": "data/silver/silver.parquet",
    "nasional": "data/gold/tabel_nasional_periode_x_seri.csv",
}


def _baca(jalur: str) -> pd.DataFrame:
    if jalur.endswith(".parquet"):
        return pd.read_parquet(jalur)
    return pd.read_csv(jalur)


def muat_ke_sql():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(DB_PATH)
    con.execute(Path(SKEMA).read_text(encoding="utf-8")).fetchall()
    for tabel, jalur in TABEL.items():
        df = _baca(jalur)
        cur = con.cursor()  # koneksi terpisah per tabel supaya tidak bentrok
        cur.register("sumber_df", df)
        cur.execute(f"DELETE FROM {tabel}").fetchall()
        cur.execute(f"INSERT INTO {tabel} SELECT * FROM sumber_df").fetchall()
        n_sql = cur.execute(f"SELECT COUNT(*) FROM {tabel}").fetchall()[0][0]
        cur.unregister("sumber_df")
        cur.close()
        assert n_sql == len(df), f"{tabel}: SQL {n_sql} vs sumber {len(df)}"
        print(f"sql        : {tabel} {n_sql} baris OK")
    con.close()


if __name__ == "__main__":
    muat_ke_sql()