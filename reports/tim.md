# Laporan tim — <Nama tim>, kasus 04 Kesehatan SDG (Malaria, Hipertensi/PTM, dan Tembakau)

Satu dokumen bersama, enam bagian. Angka harus dapat ditarik ulang dari `data/silver`, `data/gold`,
dan `log-keputusan.csv` yang sudah di-*commit*.

## Ringkasan
Kasus, seri yang ditangani, dan satu kalimat temuan utama tentang kualitas datanya.

## Data dan lineage
Sumber dan format mentah, jumlah berkas, cara `_berkas_raw`/`_sha256_raw` dibentuk, dan hasil tarik
ulang API (bila dilakukan): apa yang berubah sejak snapshot 17–20 Oktober 2026.

## Masalah data dan penanganannya

Selama proses ekstraksi, pemprofilan, validasi skema, dan rekonsiliasi pada **Sprint 1** (total **1.058 baris** bersih pada tabel Silver yang terdiri atas **913 baris** seri utama BPS dan **145 baris** seri pembanding WHO GHO serta World Bank WDI), ditemukan beberapa kategori masalah kualitas dan struktur data sebagai berikut:

| Kategori Masalah | Seri Terdampak | Temuan & Jumlah Baris Terdampak | Keputusan Penanganan | Alternatif yang Ditolak | ID Log |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Nilai Hilang (*Missing Values*)** | `SH.MLR.INCD.P3` (WDI) | **41 baris** bernilai `null` dari total 66 observasi mentah (menyisakan **25 baris** valid tahun 2000–2024). | Membuang baris dengan `nilai = null` saat ekstraksi ke Silver karena seri sudah terwakili utuh 1 observasi per tahun (2000–2024). | Mengisi nilai kosong dengan nol (`0`) atau interpolasi buatan yang dapat mendistorsi tren historis. | — *(Ekstraksi)* |
| **Outlier Ekstrem Asli (Epidemiologis & Regional)** | `var1393`, `var1480`, `var1435` | Deteksi awal IQR/z-score menandai **140 titik** dari 1.826 rekaman mentah dua snapshot (`reports/calon-anomali-seri-utama.csv`). Pada Silver kanonik: **416 baris** `var1393` (maks Papua `80,05` dan Papua Barat `73,21` per 1.000 penduduk; 33 baris `0,00`), **104 baris** `var1480` (rentang `24,65%–44,1%`, maks Kalimantan Selatan `44,1%`), dan **393 baris** `var1435` (rentang `17,91%–36,56%`, maks Gorontalo `36,56%`). | Seluruh nilai asli **dipertahankan tanpa perubahan**; khusus insidens malaria dengan nilai `> 20,0` ditandai melalui kolom boolean `tandai_outlier = True` pada validasi Silver. | Menghapus observasi ekstrem atau melakukan pemotongan (*winsorizing*) di atas persentil ke-95. | `K-001`, `K-002`, `K-003` |
| **Patahan Seri Administratif (Pemekaran Provinsi)** | `var1393`, `var1480`, `var1435` | Memengaruhi seluruh **913 baris** panel BPS akibat penambahan entitas wilayah administratif: dari **34 menjadi 35 wilayah** mulai 2014 (pemekaran Kalimantan Utara) dan dari **35 menjadi 39 wilayah** mulai 2024 pada `var1435` (4 Daerah Otonomi Baru Papua). | Menandai tahun transisi pemekaran sebagai patahan seri struktural agar analisis deret waktu tingkat provinsi tidak keliru menganggap kemunculan entitas baru sebagai lonjakan data. | Membuang provinsi hasil pemekaran atau menganggap kemunculan entitas baru sebagai galat input. | `K-004` |
| **Patahan Seri Cakupan Survei** | `var1480` | **1 baris** khusus pada tahun **2016** yang hanya memuat agregat nasional (`INDONESIA = 30,9%`, bersumber dari Sirkesnas), berbeda dari panel lengkap **34–35 wilayah** pada tahun Riskesdas (`2007`, `2013`, `2018` yang berjumlah 103 baris). | Mempertahankan baris tahun 2016 sebagai titik agregat nasional dan menandainya sebagai patahan cakupan agar tidak dicampur dalam analisis panel tingkat provinsi. | Menghapus titik tahun 2016 atau melakukan imputasi mundur/maju untuk 34 provinsi dari angka nasional. | `K-005` |
| **Duplikasi Antar-Snapshot & Revisi Rilis** | Semua seri (`913 baris` BPS) | Berkas mentah BPS tersimpan dalam dua snapshot (CSV dan JSON, total **1.826 baris** mentah untuk 913 observasi unik). | Menerapkan deduplikasi berdasarkan kunci primer `(sumber, seri_kode, wilayah_kode, periode, rincian)`: nilai identik dipertahankan **1 baris kanonik** (`0` baris nilai diubah), sedangkan perbedaan nilai antar-tanggal rilis dicatat sebagai revisi dan dipilih snapshot terbaru. | Membiarkan baris ganda masuk ke tabel Silver atau menghapus seluruh rekaman yang muncul dua kali. | `K-007` |
| **Audit Galat Input & Validasi Domain** | `var1393`, `var1480`, `var1435` | Pemeriksaan batas domain pada **913 baris** BPS menemukan **0 baris** galat input (tidak ada nilai negatif, persentase `> 100%`, atau salah ketik satuan). | Tidak melakukan perubahan nilai observasi; aturan batas domain (`0–100` untuk prevalensi, `>= 0` untuk malaria) dikunci dalam skema validasi `pandera`. | Melakukan koreksi nilai secara manual tanpa bukti galat pencatatan sumber. | `K-006` |
| **Titik Proyeksi Masa Depan & Celah Panel Tahunan** | `M_Est_tob_curr_std`, `var1480`, `var1435` | • `M_Est_tob_curr_std` (WHO GHO) memiliki **30 baris** pada 10 tahun diskrit (`2000–2030`), termasuk **3 baris** proyeksi tahun **2030** (`TOTAL`, `MALE`, `FEMALE`).<br>• Panel BPS tidak seragam tahunannya: `var1393` kontinu 12 tahun (`2010–2021`), `var1435` kontinu 11 tahun (`2015–2025`), sedangkan `var1480` hanya tersedia pada **4 titik survei** (`2007`, `2013`, `2016`, `2018`). | Menandai baris WHO dengan `periode > 2025` menggunakan `tandai_proyeksi_who = True` agar tidak masuk ke rekonsiliasi historis, serta membatasi tabel rekonsiliasi nasional hanya pada **15 tahun unik yang benar-benar beririsan** (`2007`, `2010–2022`, `2025`). | Mengikutsertakan proyeksi tahun 2030 ke perbandingan historis atau melakukan interpolasi linear pada celah tahun survei Riskesdas (`var1480`). | — *(Validasi & Rekonsiliasi)* |
| **Perbedaan Definisi & Granularitas Antar-Sumber** | `var1480` vs `NCDMORT3070`; `var1435` vs `M_Est_tob_curr_std` | • `var1480` mengukur prevalensi tekanan darah tinggi (`%`), sedangkan `NCDMORT3070` mengukur probabilitas kematian dini akibat 4 PTM utama usia 30–70 tahun (`%`).<br>• `var1435` merupakan prevalensi kasar (*crude*), sedangkan `M_Est_tob_curr_std` terstandardisasi umur (*age-standardized*). | Mengelompokkan pasangan ke dalam kategori keterbandingan eksplisit (`definisi berbeda` untuk PTM dan `metode berbeda` untuk tembakau) pada `reports/pasangan_rekonsiliasi.md` dan memfilter rincian agregat `TOTAL` / `TOTAL|YEARS30-69`. | Membandingkan nilai mentah secara langsung sebagai indikator yang identik tanpa catatan metodologi. | — *(Rekonsiliasi)* |

Seluruh angka pada tabel di atas dapat ditarik ulang secara otomatis dari lapisan Silver (`src.extract.ekstrak_semua()` dan `src.validasi.aturan.tandai_silver()`) serta `log-keputusan.csv` dengan menjalankan `python -m src.ringkasan_sprint1`.

## Integrasi dan rekonsiliasi
Seri utama vs pembanding nasional: selisih, penjelasannya (definisi, metode, vintage, granularitas),
dan hasil analisis revisi dari arsip WDI.

## Validasi dan reproduksibilitas
Skema validasi (aturan, hasil lolos/gagal), waktu `python pipeline.py` dari nol, perbandingan pandas
vs DuckDB/Dask, dan keterbatasan yang tersisa.

## Pembagian kerja
| Anggota | NIM | Komponen | Tugas sampingan | Bagian laporan yang ditulis |
| Talitha Justine | 124450076 | Integrasi, penyimpanan, dan skala | Analis Utama | Masalah data dan penanganannya |
### Bantuan Pengerjaan Lintas Anggota — Sprint 1
- **Kartu #7 (Tahap 3 — Grid 38 Provinsi × Periode & Strategi Missing):** Djofy Prianda Banu (`124450117`) membantu menyusun dan menjalankan modul `src/silver/grid.py`, menghasilkan laporan `reports/kelengkapan-panel.md` dan `reports/kelengkapan-panel.csv`, serta mencatat keputusan `K-015` s.d. `K-019` di `log-keputusan.csv` atas nama pemilik tugas Jihan Putri Yani (`121450161`).
