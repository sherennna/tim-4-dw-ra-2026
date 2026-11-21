New-Item -ItemType Directory -Force -Path "reports" | Out-Null
@'
# Daftar Pasangan Rekonsiliasi & Catatan Keterbandingan (Persiapan Tahap 6)

- **Tabel Nasional (Periode × Seri):** `data/gold/tabel_nasional_periode_x_seri.csv`
- **Cakupan Wilayah:** Nasional (`INDONESIA` / `IDN`)
- **Total Pasangan Rekonsiliasi:** 4 pasangan (dalam 3 kelompok indikator SDG)
- **Total Periode Beririsan (tahun unik):** 15 tahun (`2007`, `2010–2022`, `2025`)

---

## Daftar Pasangan Rekonsiliasi

| ID | Seri Utama (BPS) | Seri Pembanding | Sumber | Kategori Keterbandingan | Jumlah & Daftar Tahun Beririsan |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **P-01a** | `var1393` (Kejadian malaria per 1.000 orang) | `MALARIA_EST_INCIDENCE` | WHO GHO | Perlu verifikasi penyebut (*penduduk berisiko vs seluruh penduduk*) | **12 tahun:** `2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021` |
| **P-01b** | `var1393` (Kejadian malaria per 1.000 orang) | `SH.MLR.INCD.P3` | World Bank WDI | Perlu verifikasi penyebut (*penduduk berisiko vs seluruh penduduk*) | **12 tahun:** `2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021` |
| **P-02** | `var1435` (Prevalensi merokok) | `M_Est_tob_curr_std` | WHO GHO | Beda metode (*survei kasar vs estimasi/proyeksi terstandardisasi umur*) | **5 tahun:** `2015, 2020, 2021, 2022, 2025` *(tahun `2030` pada WHO adalah proyeksi)* |
| **P-03** | `var1480` (Prevalensi tekanan darah tinggi) | `NCDMORT3070` | WHO GHO | **Definisi berbeda** (*prevalensi vs probabilitas kematian*) | **4 tahun:** `2007, 2013, 2016, 2018` |

---

## Catatan Keterbandingan Detail per Kasus

### 1. Insidensi Malaria: `var1393` vs WHO `MALARIA_EST_INCIDENCE` vs WDI `SH.MLR.INCD.P3`
* **Kesamaan Indikator:** Ketiganya mengukur insidensi malaria per 1.000 penduduk (SDG 3.3.3).
* **Verifikasi Penyebut (Denominator):**
  * **WHO (`MALARIA_EST_INCIDENCE`) & WDI (`SH.MLR.INCD.P3`):** Berdasarkan metadata WHO Global Health Observatory dan World Bank WDI (yang bersumber dari WHO), penyebut yang dipakai adalah **penduduk berisiko (*population at risk*)** per 1.000 orang.
  * **BPS (`var1393`):** Menggunakan angka *Annual Parasite Incidence* (API) nasional Kemenkes/BPS. Perlu memastikan konsistensi penyebutnya (penduduk berisiko di wilayah endemis vs total populasi Indonesia), karena perbedaan penyebut akan menggeser skala nilai secara sistematis.
* **Catatan Rekonsiliasi:** Nilai `var1393` dan `MALARIA_EST_INCIDENCE`/`SH.MLR.INCD.P3` beririsan pada **12 tahun (`2010–2021`)**. Perbandingan langsung di Sprint 2 harus memverifikasi kesamaan penyebut terlebih dahulu.

### 2. Prevalensi Penggunaan Tembakau: `var1435` vs WHO `M_Est_tob_curr_std`
* **Perbedaan Metodologi & Standardisasi:**
  * **WHO (`M_Est_tob_curr_std`):** Berdasarkan metadata WHO (`Indicator.json` / `ddiindicators`), seri ini merupakan **estimasi hasil pemodelan WHO yang terstandardisasi umur (*age-standardized prevalence estimate*)** pada penduduk usia 15+ tahun, bukan angka mentah hasil satu survei.
  * **BPS (`var1435`):** Merupakan prevalensi merokok hasil survei nasional (Riskesdas/Susenas/SKI) yang bersifat **kasar (*crude prevalence*, tidak terstandardisasi umur)** dan mencakup penggunaan rokok tembakau (*smoking*), sedangkan indikator WHO mencakup seluruh produk tembakau (*current tobacco use*).
* **Pemisahan Estimasi Historis vs Proyeksi:**
  * Deret waktu WHO `M_Est_tob_curr_std` mencakup tahun hingga **`2030`**, melewati tahun observasi survei terakhir.
  * Tahun hingga **`2022`/`2025`** merupakan **estimasi model** berbasis data survei historis, sedangkan tahun **`2030`** adalah **proyeksi tren**.
  * Rekonsiliasi dengan `var1435` dibatasi hanya pada **5 titik tahun beririsan (`2015, 2020, 2021, 2022, 2025`)** dan tidak mengikutsertakan titik proyeksi `2030`.

### 3. Penyakit Tidak Menular (PTM): `var1480` vs WHO `NCDMORT3070`
* **Kategorisasi:** **Definisi berbeda (*Different Definition*)**.
* **Alasan Metodologis:**
  * **BPS (`var1480`):** Mengukur **prevalensi tekanan darah tinggi (hipertensi)** pada penduduk (indikator morbiditas/faktor risiko PTM).
  * **WHO (`NCDMORT3070`):** Mengukur **probabilitas kematian tanpa syarat (*unconditional probability of dying*)** antara usia 30 hingga 70 tahun akibat 4 PTM utama (penyakit kardiovaskular, kanker, diabetes, atau penyakit pernapasan kronis — indikator SDG 3.4.1).
* **Catatan Rekonsiliasi:** Meskipun berada di bawah klaster SDG 3.4 (PTM), keduanya mengukur fenomena dan satuan yang berbeda secara fundamental (prevalensi hipertensi vs probabilitas kematian 4 PTM). Oleh karena itu, pasangan ini dikategorikan sebagai **definisi berbeda** dan tidak dilakukan rekonsiliasi selisih nilai secara langsung.
'@ | Set-Content -Encoding UTF8 "reports/pasangan_rekonsiliasi.md"

git add -f data/gold/tabel_nasional_periode_x_seri.csv reports/pasangan_rekonsiliasi.md src/persiapan_tahap6.py results/124450076/metrics.json
git status -s