# Profil Seri Pembanding Nasional (Tahap 2)

Dokumen ini memuat profil ketersediaan periode, rincian (disagregasi), satuan, serta evaluasi kandidat rincian yang sebanding dengan seri utama BPS untuk proses rekonsiliasi (Tahap 6).

## 1. Tabel Ketersediaan Seri Pembanding Nasional

| Kode Seri | Sumber & Nama Indikator | Periode Tersedia | Rincian / Disagregasi Tersedia | Satuan | Seri Utama BPS & Tahun Beririsan |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MALARIA_EST_INCIDENCE** | **WHO GHO** — *Malaria cases* (442CEA8_MALARIA_EST_INCIDENCE.csv) | 2000–2023 (tahunan, 24 titik) | Agregat nasional (Indonesia), tanpa rincian jenis kelamin/umur | Kasus per 1.000 populasi berisiko (RATE_PER_1000_N) | **BPS ar1393** (2010–2021) — beririsan penuh **12 tahun (2010–2021)** |
| **SH.MLR.INCD.P3** | **World Bank WDI** — *Incidence of malaria (per 1,000 population at risk)* | 2000–2024 (tahunan, 25 titik) | Agregat nasional (IDN), tanpa rincian jenis kelamin/umur | Kasus per 1.000 populasi berisiko | **BPS ar1393** (2010–2021) — beririsan penuh **12 tahun (2010–2021)** |
| **NCDMORT3070** | **WHO GHO** — *Non-communicable diseases deaths (age 30 to 70)* (1F96863_NCDMORT3070.csv) | 2000–2021 (tahunan, 22 titik) | • DIM_SEX: TOTAL, MALE, FEMALE<br>• DIM_AGE: YEARS30-69 | Persentase / probabilitas kematian dini usia 30–70 tahun (RATE_PER_100_N) | **BPS ar1480** (2007–2018) — beririsan penuh **12 tahun (2007–2018)** |
| **M_Est_tob_curr_std** | **WHO GHO** — *Tobacco use* (75DDA77_M_Est_tob_curr_std.csv) | 2000–2030 *(diskrit: 2000, 2005, 2007, 2010, 2015, 2020, 2021, 2022, 2025, 2030)* | • DIM_SEX: TOTAL, MALE, FEMALE<br>• Standarisasi usia (ge-standardized) | Persentase populasi (PERCENT_POP_N) | **BPS ar1435** (2015–2025) — beririsan pada **5 titik tahun (2015, 2020, 2021, 2022, 2025)** |

---

## 2. Kandidat Rincian Sebanding & Alasan Pemilihan

1. **Insidens Malaria (MALARIA_EST_INCIDENCE & SH.MLR.INCD.P3 vs BPS ar1393)**
   * **Kandidat terpilih:** Agregat nasional tunggal (tanpa filter dimensi tambahan).
   * **Alasan:** Kedua sumber pembanding hanya menyediakan angka agregat nasional (Indonesia / IDN) dengan satuan identik (*per 1.000 penduduk berisiko*), sehingga langsung sebanding dengan angka agregat nasional maupun rata-rata tertimbang provinsi BPS ar1393 pada rentang **2010–2021**.

2. **Kematian Dini PTM (NCDMORT3070 vs BPS ar1480)**
   * **Kandidat terpilih:** **DIM_SEX = TOTAL** dan **DIM_AGE = YEARS30-69**.
   * **Alasan:** Seri utama BPS ar1480 menyajikan angka gabungan penduduk (tanpa pemisahan laki-laki/perempuan). Menggunakan DIM_SEX = TOTAL memastikan kesetaraan populasi penyebut, sementara DIM_AGE = YEARS30-69 adalah satu-satunya kelompok umur standar SDG 3.4.1 pada rentang irisan **2007–2018**.

3. **Prevalensi Merokok (M_Est_tob_curr_std vs BPS ar1435)**
   * **Kandidat terpilih:** **DIM_SEX = TOTAL**.
   * **Alasan:** Data BPS ar1435 melaporkan prevalensi merokok penduduk secara agregat tanpa pemisahan jenis kelamin, sehingga DIM_SEX = TOTAL menjadi pasangan yang tepat untuk dibandingkan pada **5 tahun yang beririsan (2015, 2020, 2021, 2022, 2025)**.
   * **Catatan metodologis untuk Tahap 6:** Estimasi WHO (M_Est_tob_curr_std) merupakan angka *age-standardized* (terstandar usia, penduduk >= 15 tahun), sedangkan survei BPS merupakan prevalensi kasar (*crude rate*). Perbedaan struktur usia ini perlu dicatat sebagai faktor penjelas selisih level saat rekonsiliasi.
