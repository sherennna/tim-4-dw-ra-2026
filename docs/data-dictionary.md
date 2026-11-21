# Data dictionary — Kelompok 4 (Kasus 04: Penyakit menular dan faktor risiko)

Satu tabel per keluaran (`Silver` pada Sprint 1; tabel `Gold` ditambahkan pada Sprint 2–3). Setiap baris pada lapisan Silver merepresentasikan satu observasi unik per kombinasi kunci primer `['sumber', 'seri_kode', 'wilayah_kode', 'periode', 'rincian', '_berkas_raw']`.

## data/silver/silver.parquet

| Kolom | Tipe | Satuan/format | Boleh kosong | Rentang atau nilai sah | Asal (berkas/aturan) | Keterangan |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `sumber` | `string` | — | tidak | `bps`, `who_gho`, `wdi` | Nama direktori sumber di `data/raw/` (`src/ekstraksi/`) | Identitas penyedia dataset asal. |
| `seri_kode` | `string` | — | tidak | `var1393`, `var1480`, `var1435`, `MALARIA_EST_INCIDENCE`, `NCDMORT3070`, `M_Est_tob_curr_std`, `SH.MLR.INCD.P3` | Kode variabel/indikator asal (`var` BPS, `IND_CODE` WHO GHO, `indicator.id` WDI) & `log-keputusan.csv` | Kode seri indikator kanonik Kasus 04. |
| `wilayah_kode` | `int64` | kode BPS × 100 | tidak | `9999` (nasional) atau `1100`–`9600` (provinsi) | Pemetaan `vervar` BPS, `DIM_GEO_CODE_M49` (`360` -> `9999`) WHO, `countryiso3code` (`IDN` -> `9999`) WDI (`src/common/skema.py`, `log-keputusan.csv` `K-004`, `K-005`) | Kode wilayah numerik baku Indonesia dan provinsi. |
| `nama_wilayah` | `string` | — | tidak | Nama provinsi Indonesia atau `INDONESIA` / `Indonesia` | Label `vervar` BPS, `GEO_NAME_SHORT` WHO GHO, `country.value` WDI | Nama wilayah geografis setelah penyeragaman penulisan. |
| `periode` | `string` | `YYYY` | tidak | `2000`–`2030` (4 digit tahun) | Kolom `tahun` BPS, `DIM_TIME` WHO GHO, `date` WDI | Tahun observasi dalam format baku sesuai `jenis_periode`. |
| `jenis_periode` | `string` | — | tidak | `tahun` (pola `^\d{4}$`) | Metadata frekuensi rilis masing-masing seri (`src/common/skema.py`) | Granularitas waktu; seluruh seri Kasus 04 bersifat tahunan. |
| `rincian` | `string` | — | tidak | `total` atau kombinasi `DIM_*` (mis. `DIM_SEX=TOTAL;DIM_AGE=YEARS30-69`) | `turvar` BPS dan kolom `DIM_*` terisi pada CSV WHO GHO (`docs/profil-seri-pembanding.md`) | Dimensi disagregasi tambahan selain wilayah dan periode. |
| `nilai` | `float64` | Mengikuti kolom `satuan` | tidak | `0`–`100` untuk seri prevalensi (`var1480`, `var1435`, `M_Est_tob_curr_std`); `>= 0` untuk insidens malaria (`var1393`, `MALARIA_EST_INCIDENCE`, `SH.MLR.INCD.P3`) dan `NCDMORT3070` | Kolom `nilai` / `datacontent` BPS, `*_N` WHO GHO, `value` WDI (`src/validasi/aturan.py`) | Nilai numerik hasil observasi/estimasi; sel kosong tidak disimpan di Silver. |
| `satuan` | `string` | — | tidak | `per 1.000 penduduk`, `persen` | Metadata `manifest_asal.json` / judul `var` BPS, prefiks kolom nilai WHO (`RATE_PER_1000_N`, `RATE_PER_100_N`, `PERCENT_POP_N`), metadata indikator WDI | Satuan pengukuran baku per seri (`per 1.000 penduduk` untuk malaria; `persen` untuk hipertensi, merokok, dan kematian dini PTM). |
| `_berkas_raw` | `string` | jalur relatif | tidak | Jalur berkas yang terdaftar di `data/raw/MANIFEST.csv` | Ditempelkan saat Tahap 1 ekstraksi (`src/ekstraksi/`) | Jejak berkas mentah asal di dalam folder `data/raw/`. |
| `_sha256_raw` | `string` | 64 karakter hex | tidak | Hash SHA-256 valid yang cocok dengan `data/raw/MANIFEST.csv` | `src.common.manifest.sha256_raw()` (`src/common/skema.py`) | Sidik integritas berkas mentah asal (*data lineage*). |
| `tandai_outlier` | `bool` | — | tidak | `True`, `False` | Aturan validasi `src/validasi/aturan.py` (`tandai_silver`) & `log-keputusan.csv` (`K-001` s.d. `K-003`) | Menandai outlier ekstrem insidens malaria (`nilai > 20` per 1.000 penduduk) tanpa menghapus fakta epidemiologis. |
| `tandai_proyeksi_who` | `bool` | — | tidak | `True`, `False` | Aturan validasi `src/validasi/aturan.py` (`tandai_silver`) & `docs/profil-seri-pembanding.md` | Menandai baris estimasi proyeksi masa depan WHO (`periode > 2025`) agar dikecualikan dari tabel rekonsiliasi. |

### Contoh Penelusuran Satu Baris Silver ke Berkas Mentah (*Lineage*)

Berikut contoh penelusuran satu baris observasi pada `data/silver/silver.parquet` hingga ke berkas mentahnya:

| `sumber` | `seri_kode` | `wilayah_kode` | `nama_wilayah` | `periode` | `jenis_periode` | `rincian` | `nilai` | `satuan` | `_berkas_raw` | `_sha256_raw` | `tandai_outlier` | `tandai_proyeksi_who` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `bps` | `var1393` | `9400` | `PAPUA` | `2021` | `tahun` | `total` | `80.05` | `per 1.000 penduduk` | `bps/2026-10-20/sdg3_3_3_3_v1393.csv` | `87863ec605966817a778c9c56383fbaf8e9d2adf898a7caac3ab67267d988492` | `True` | `False` |

**Langkah verifikasi penelusuran:**
1. **Rujuk berkas asal melalui `_berkas_raw`:** Jalur `bps/2026-10-20/sdg3_3_3_3_v1393.csv` mengarah langsung ke berkas `data/raw/bps/2026-10-20/sdg3_3_3_3_v1393.csv`.
2. **Cocokkan sidik SHA-256 pada `_sha256_raw`:** Nilai `87863ec605966817a778c9c56383fbaf8e9d2adf898a7caac3ab67267d988492` diverifikasi identik dengan entri `bps/2026-10-20/sdg3_3_3_3_v1393.csv` di `data/raw/MANIFEST.csv` melalui `src.common.manifest.periksa()`.
3. **Cocokkan nilai mentah dan keputusan log:** Pada berkas `data/raw/bps/2026-10-20/sdg3_3_3_3_v1393.csv` baris untuk `PAPUA` (`wilayah_id = 9400`, tahun `2021`), tercatat nilai insidens malaria sebesar `80.05` per 1.000 penduduk. Sesuai keputusan `K-001` di `log-keputusan.csv`, nilai ekstrem ini dipertahankan dan ditandai `tandai_outlier = True`.

## data/gold/<tabel>.parquet

*Akan dilengkapi pada Sprint 2–3 setelah tabel panel provinsi dan tabel rekonsiliasi nasional terbentuk.*

| Kolom | Tipe | Satuan/format | Boleh kosong | Rentang atau nilai sah | Asal (berkas/aturan) | Keterangan |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |