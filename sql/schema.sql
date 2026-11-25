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

CREATE TABLE IF NOT EXISTS nasional (
    periode                 INTEGER NOT NULL PRIMARY KEY,
    var1393                 DOUBLE,
    MALARIA_EST_INCIDENCE   DOUBLE,
    "SH.MLR.INCD.P3"        DOUBLE,
    var1435                 DOUBLE,
    M_Est_tob_curr_std      DOUBLE,
    var1480                 DOUBLE,
    NCDMORT3070             DOUBLE
);