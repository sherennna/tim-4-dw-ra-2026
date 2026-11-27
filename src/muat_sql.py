"""Tahap 5: Pemuatan lapisan Silver dan Gold ke basis data relasional DuckDB."""
from pathlib import Path
import duckdb
import pandas as pd

DB_PATH = "data/db/capstone.duckdb"
SKEMA = "sql/schema.sql"

# Pemetaan 4 tabel SQL -> berkas Parquet sumber (Silver & Gold)
TABEL = {
    "silver": "data/silver/silver.parquet",
    "panel_provinsi": "data/gold/panel_provinsi.parquet",
    "nasional": "data/gold/nasional.parquet",
    "rekonsiliasi_nasional": "data/gold/rekonsiliasi_nasional.parquet",
}


def _baca(jalur: str) -> pd.DataFrame:
    if jalur.endswith(".parquet"):
        return pd.read_parquet(jalur)
    return pd.read_csv(jalur)


def muat_ke_sql(db_path: str = DB_PATH, skema_path: str = SKEMA) -> dict[str, int]:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(db_path)

    # Buat ulang tabel sesuai DDL terbaru agar perubahan skema/PK selalu sinkron
    for nama_tabel in reversed(list(TABEL.keys())):
        con.execute(f"DROP TABLE IF EXISTS {nama_tabel}").fetchall()
    con.execute(Path(skema_path).read_text(encoding="utf-8")).fetchall()

    ringkasan: dict[str, int] = {}
    for tabel, jalur in TABEL.items():
        df = _baca(jalur)
        cur = con.cursor()
        cur.register("sumber_df", df)
        cur.execute(f"INSERT INTO {tabel} SELECT * FROM sumber_df").fetchall()
        n_sql = int(cur.execute(f"SELECT COUNT(*) FROM {tabel}").fetchall()[0][0])
        cur.unregister("sumber_df")
        cur.close()
        assert n_sql == len(df), f"{tabel}: jumlah baris SQL ({n_sql}) != sumber ({len(df)})"
        ringkasan[tabel] = n_sql
        print(f"sql        : {tabel:<22} {n_sql} baris OK")

    con.close()
    return ringkasan


if __name__ == "__main__":
    muat_ke_sql()
