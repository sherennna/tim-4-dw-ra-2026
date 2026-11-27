"""Pengujian Tahap 5: Verifikasi skema DDL, kunci primer, dan jumlah baris 4 tabel SQL vs Parquet."""
from pathlib import Path
import duckdb
import pandas as pd

DB_PATH = Path("data/db/capstone.duckdb")

SPESIFIKASI_TABEL = {
    "silver": {
        "parquet": Path("data/silver/silver.parquet"),
        "pk": ["sumber", "seri_kode", "wilayah_kode", "periode", "rincian"],
    },
    "panel_provinsi": {
        "parquet": Path("data/gold/panel_provinsi.parquet"),
        "pk": ["provinsi_kode", "periode", "indikator"],
    },
    "nasional": {
        "parquet": Path("data/gold/nasional.parquet"),
        "pk": ["sumber", "indikator", "rincian", "periode"],
    },
    "rekonsiliasi_nasional": {
        "parquet": Path("data/gold/rekonsiliasi_nasional.parquet"),
        "pk": ["pasangan", "periode"],
    },
}


def uji_semua_tabel_sql() -> None:
    assert DB_PATH.exists(), f"Basis data tidak ditemukan: {DB_PATH}"
    con = duckdb.connect(str(DB_PATH), read_only=True)

    daftar_tabel_db = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    for nama_tabel, spec in SPESIFIKASI_TABEL.items():
        assert nama_tabel in daftar_tabel_db, f"Tabel {nama_tabel} tidak ada di DuckDB!"

        df_pq = pd.read_parquet(spec["parquet"])
        n_sql = int(con.execute(f"SELECT COUNT(*) FROM {nama_tabel}").fetchone()[0])
        assert n_sql == len(df_pq), f"{nama_tabel}: SQL={n_sql} != Parquet={len(df_pq)}"

        info_kolom = con.execute(f"PRAGMA table_info('{nama_tabel}')").fetchall()
        kolom_pk_db = [baris[1] for baris in info_kolom if baris[5]]
        assert kolom_pk_db == spec["pk"], f"{nama_tabel}: PK SQL {kolom_pk_db} != {spec['pk']}"

        pk_expr = ", ".join(spec["pk"])
        n_distinct = int(
            con.execute(f"SELECT COUNT(*) FROM (SELECT DISTINCT {pk_expr} FROM {nama_tabel})").fetchone()[0]
        )
        assert n_distinct == n_sql, f"{nama_tabel}: ditemukan duplikat pada PK ({pk_expr})"

        print(f"[LOLOS] {nama_tabel:<22} | baris SQL={n_sql:<4} == Parquet={len(df_pq):<4} | PK={spec['pk']}")

    con.close()
    print("\nSemua 4 tabel SQL lolos uji skema, kunci primer, dan kesamaan jumlah baris.")


if __name__ == "__main__":
    uji_semua_tabel_sql()
