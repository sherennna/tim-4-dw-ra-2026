-- DDL Lapisan Silver dan Gold (Tahap 5 - Kasus 04)
-- Dialek: DuckDB SQL (kompatibel standar ANSI SQL)

CREATE TABLE IF NOT EXISTS silver (
    sumber               TEXT    NOT NULL,
    seri_kode            TEXT    NOT NULL,
    wilayah_kode         BIGINT  NOT NULL,
    nama_wilayah         TEXT,
    periode              TEXT    NOT NULL,
    jenis_periode        TEXT    NOT NULL,
    rincian              TEXT    NOT NULL,
    nilai                DOUBLE,
    satuan               TEXT,
    _berkas_raw          TEXT    NOT NULL,
    _sha256_raw          TEXT    NOT NULL,
    tandai_outlier       BOOLEAN NOT NULL,
    tandai_proyeksi_who  BOOLEAN NOT NULL,
    PRIMARY KEY (sumber, seri_kode, wilayah_kode, periode, rincian)
);

CREATE TABLE IF NOT EXISTS panel_provinsi (
    provinsi_kode         BIGINT  NOT NULL,
    provinsi              TEXT    NOT NULL,
    periode               INTEGER NOT NULL,
    indikator             TEXT    NOT NULL,
    nama_indikator        TEXT    NOT NULL,
    nilai                 DOUBLE  NOT NULL,
    satuan                TEXT    NOT NULL,
    nilai_log1p           DOUBLE,
    flag_sel              TEXT    NOT NULL,
    silver_row_id         BIGINT  NOT NULL,
    silver_row_id_setara  TEXT    NOT NULL,
    berkas_raw            TEXT    NOT NULL,
    sha256_raw            TEXT    NOT NULL,
    PRIMARY KEY (provinsi_kode, periode, indikator)
);

CREATE TABLE IF NOT EXISTS nasional (
    sumber                TEXT    NOT NULL,
    indikator             TEXT    NOT NULL,
    rincian               TEXT    NOT NULL,
    periode               INTEGER NOT NULL,
    nilai                 DOUBLE  NOT NULL,
    satuan                TEXT    NOT NULL,
    nilai_log1p           DOUBLE,
    flag_sel              TEXT    NOT NULL,
    silver_row_id         BIGINT  NOT NULL,
    silver_row_id_setara  TEXT    NOT NULL,
    berkas_raw            TEXT    NOT NULL,
    sha256_raw            TEXT    NOT NULL,
    PRIMARY KEY (sumber, indikator, rincian, periode)
);

CREATE TABLE IF NOT EXISTS rekonsiliasi_nasional (
    pasangan                TEXT    NOT NULL,
    seri_utama              TEXT    NOT NULL,
    seri_pembanding         TEXT    NOT NULL,
    periode                 INTEGER NOT NULL,
    nilai_seri_utama        DOUBLE,
    satuan_utama            TEXT,
    nilai_pembanding        DOUBLE,
    satuan_pembanding       TEXT,
    selisih                 DOUBLE,
    status_pasangan         TEXT    NOT NULL,
    jenis_nilai_pembanding  TEXT    NOT NULL,
    kategori_penjelasan     TEXT,
    penjelasan_dan_bukti    TEXT,
    PRIMARY KEY (pasangan, periode)
);
