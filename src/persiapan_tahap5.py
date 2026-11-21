import duckdb
import pandas as pd
from pathlib import Path
from src.extract import ekstrak_semua

# 1. Ekstrak data dari lapisan Bronze menggunakan fungsi standar tim
df = ekstrak_semua()

# 2. Normalisasi tipe data sebelum pemuatan ke lapisan Silver
df_silver = df.copy()
df_silver["sumber"] = df_silver["sumber"].astype(str).str.strip()
df_silver["seri_kode"] = df_silver["seri_kode"].astype(str).str.strip()
df_silver["wilayah_kode"] = df_silver["wilayah_kode"].astype(str).str.strip()
df_silver["nama_wilayah"] = df_silver["nama_wilayah"].astype(str).str.strip()
df_silver["periode"] = pd.to_numeric(df_silver["periode"], errors="coerce").astype("Int64")
df_silver["jenis_periode"] = df_silver["jenis_periode"].astype(str).str.strip()
df_silver["rincian"] = df_silver["rincian"].fillna("Tidak ada").astype(str).str.strip()
df_silver["nilai"] = pd.to_numeric(df_silver["nilai"], errors="coerce")
df_silver["satuan"] = df_silver["satuan"].fillna("").astype(str).str.strip()
df_silver["_berkas_raw"] = df_silver["_berkas_raw"].astype(str).str.strip()
df_silver["_sha256_raw"] = df_silver["_sha256_raw"].astype(str).str.strip()

# Buang baris dengan kunci primer atau nilai kosong, lalu deduplikasi
pk_cols = ["sumber", "seri_kode", "wilayah_kode", "periode", "rincian"]
df_silver = (
    df_silver.dropna(subset=pk_cols + ["nilai"])
    .drop_duplicates(subset=pk_cols, keep="last")
    .copy()
)
df_silver["periode"] = df_silver["periode"].astype(int)

# 3. Koneksi ke DuckDB & Eksekusi DDL Tabel Silver
db_path = Path("data/silver/sdg_kesehatan.duckdb")
db_path.parent.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(str(db_path))

ddl_sql = """
DROP TABLE IF EXISTS silver_indikator_sdg;

CREATE TABLE silver_indikator_sdg (
    sumber        VARCHAR NOT NULL,
    seri_kode     VARCHAR NOT NULL,
    wilayah_kode  VARCHAR NOT NULL,
    nama_wilayah  VARCHAR NOT NULL,
    periode       INTEGER NOT NULL,
    jenis_periode VARCHAR NOT NULL,
    rincian       VARCHAR NOT NULL,
    nilai         DOUBLE  NOT NULL,
    satuan        VARCHAR,
    _berkas_raw   VARCHAR NOT NULL,
    _sha256_raw   VARCHAR NOT NULL,
    loaded_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (sumber, seri_kode, wilayah_kode, periode, rincian)
);
"""
con.execute(ddl_sql)

# 4. Muat data Silver pertama ke dalam tabel
con.register("df_view", df_silver)
con.execute("""
    INSERT INTO silver_indikator_sdg (
        sumber, seri_kode, wilayah_kode, nama_wilayah,
        periode, jenis_periode, rincian, nilai, satuan,
        _berkas_raw, _sha256_raw
    )
    SELECT
        sumber, seri_kode, wilayah_kode, nama_wilayah,
        periode, jenis_periode, rincian, nilai, satuan,
        _berkas_raw, _sha256_raw
    FROM df_view;
""")

# 5. Verifikasi hasil pemuatan Silver pertama
total_baris = con.execute("SELECT COUNT(*) FROM silver_indikator_sdg").fetchone()[0]
ringkasan = con.execute("""
    SELECT
        sumber,
        seri_kode,
        COUNT(*) AS jumlah_baris,
        MIN(periode) AS tahun_awal,
        MAX(periode) AS tahun_akhir
    FROM silver_indikator_sdg
    GROUP BY sumber, seri_kode
    ORDER BY sumber, seri_kode
""").fetchdf()

con.close()

print("=== PEMUATAN SILVER PERTAMA BERHASIL ===")
print(f"Database              : {db_path}")
print(f"Total Baris Tersimpan : {total_baris}\n")
print(ringkasan.to_string(index=False))