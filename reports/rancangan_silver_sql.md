# Rancangan Skema SQL Silver & Pemilihan Basis Data (Persiapan Tahap 5)

- **Basis Data Terpilih:** DuckDB (`data/silver/sdg_kesehatan.duckdb`)
- **Nama Tabel Utama:** `silver_indikator_sdg`
- **Skrip DDL & Pemuat:** `src/persiapan_tahap5.py`

---

## 1. Definisi Skema Tabel (DDL)

```sql
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