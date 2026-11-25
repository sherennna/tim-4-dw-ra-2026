"""Konfigurasi Gold Tahap 4."""
NASIONAL_KODE = 9999

# seri utama BPS: nama, satuan baku (harus sama dengan Silver), log1p untuk analisis
SERI_PANEL = {
    "var1393": {"nama": "insidens_malaria",        "satuan": "per 1.000 penduduk"},
    "var1480": {"nama": "prevalensi_hipertensi",   "satuan": "persen"},
    "var1435": {"nama": "prevalensi_merokok",      "satuan": "persen"},
}
# seri pembanding WHO/WDI untuk tabel nasional
SERI_NASIONAL = {"MALARIA_EST_INCIDENCE", "SH.MLR.INCD.P3",
                 "M_Est_tob_curr_std", "NCDMORT3070"}
# seri malaria: kolom nilai_log1p terisi (nol ada di data, jadi log1p, bukan log)
SERI_LOG = {"var1393", "MALARIA_EST_INCIDENCE", "SH.MLR.INCD.P3"}
