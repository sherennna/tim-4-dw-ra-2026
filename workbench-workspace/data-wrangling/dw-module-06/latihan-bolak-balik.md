# Laporan Modul 06 — Latihan 6.2: Bolak-balik melt dan pivot
 
| Komponen | Isi |
|---|---|
| Nama | Talitha Justine |
| NIM | 124450076 |
| Tanggal pengumpulan | 04-11-2026 |
| Seed dan ukuran data | seed 2026, ukuran kecil |
| Versi Python dan pandas | Python [isi: versi Python], pandas [isi: versi pandas] |
 
## 1. Ringkasan
 
Latihan ini membuktikan dengan `DataFrame.equals` bahwa `melt` dan `pivot` mengubah bentuk tanpa mengubah makna, tetapi hanya mengembalikan tabel asal bila sel kosong dan tipe data ditangani. Pada tabel lengkap `pv_omzet` (10 provinsi × 18 bulan), bolak-balik langsung menghasilkan `equals = True`. Pada tabel berlubang (bulan 2025-01, 71 dari 80 kombinasi provinsi × kategori terisi), `melt` mengembalikan 80 baris (9 bernilai NaN) dan `equals` baru `True` setelah `dropna`, pengurutan, dan `reset_index`. Metrik `pesanan` yang awalnya `int64` kembali sebagai `float64` dan baru sama setelah `astype("int64")`. Keputusan terpentingnya: sel kosong tidak diisi 0 agar "tidak ada transaksi" tidak berubah menjadi "tercatat nol".
 
## 2. Data yang Dipakai
 
- `data/acuan/transaksi_m04.parquet` (24.000 baris × 46 kolom), `produk_m04.parquet` (850 × 15), dan `pelanggan_m04.parquet` (5.760 × 18): keluaran acuan Modul 4.
- `pv_omzet` dari Bagian C.1: omzet pesanan selesai, 10 provinsi × 18 bulan (dari `selesai`: 12.985 pesanan, Rp8.024,2 juta).
- `sel` dari Bagian C.3: omzet dan cacah pesanan per bulan × provinsi × kategori (1.309 dari 1.440 kombinasi terisi). Bulan 2025-01 dipakai untuk tabel berlubang: 71 dari 80 kombinasi provinsi × kategori terisi.
## 3. Temuan dan Bukti
 
Ringkasan percobaan (`keluaran/bolak_balik_m06.csv`):
 
| percobaan | baris_awal | baris_akhir | equals_langsung | equals_setelah_dirapikan |
|---|---:|---:|---|---|
| 1 lebar → panjang → lebar (`pv_omzet`) | 10 | 10 | True | True |
| 2 panjang → lebar → panjang, omzet (bulan 2025-01) | 71 | 80 | False | True |
| 3 panjang → lebar → panjang, pesanan (tipe) | 71 | 80 | False | True |
 
1. **Lebar → panjang → lebar** (sel TODO 1): `equals` langsung = True, dan tetap True setelah indeks dan kolom diurutkan sama. `melt()` yang dipanggil tanpa `reset_index()` menghasilkan 180 baris dengan kolom `['bulan', 'value']`: kolom provinsi hilang karena indeks tidak ikut di-`melt`.
2. **Tabel berlubang** (sel TODO 2; bulan 2025-01, provinsi × kategori): 71 baris awal → setelah `unstack` dan `melt` 80 baris (9 bernilai NaN) → setelah `dropna` dan pengurutan 71 baris. `equals` langsung = False; setelah `dropna`, pengurutan, dan `reset_index(drop=True)` = True. Bila sel kosong diisi 0, hasilnya tetap 80 baris.
3. **Tipe data** (sel TODO 3): metrik `pesanan` bertipe `int64` di tabel awal dan menjadi `float64` setelah bolak-balik; `equals` = False, dan menjadi True setelah `astype("int64")`.
## 4. Keputusan
 
| Keputusan | Alternatif yang dipertimbangkan | Mengapa tidak dipilih |
|---|---|---|
| Memakai `reset_index()` sebelum `melt` | `melt()` langsung pada tabel berindeks | Kolom provinsi (indeks) hilang dari hasil; hanya ada kolom `bulan` dan `value` |
| Sel kosong dibuang dengan `dropna` agar tabel kembali ke asal | Mengisi sel kosong dengan 0 | 0 menambah 9 baris "tercatat nol" untuk kombinasi yang tidak pernah bertransaksi; informasi berubah |
| `astype("int64")` setelah `dropna` pada metrik `pesanan` | Membiarkan tipe `float64` | `equals` menuntut tipe sama dan cacah pesanan adalah bilangan bulat |
| Pembuktian dengan `equals` setelah menyamakan urutan, NaN, dan tipe | Menganggap tabel sama bila tampak sama | `equals` ketat pada nilai, tipe, indeks, dan urutan |
 
## 5. Rekonsiliasi Jumlah Baris
 
| Langkah | Baris sebelum | Baris sesudah | Selisih | Penjelasan |
|---|---:|---:|---:|---|
| `pv_omzet` → hasil `melt` | 10 | 180 | +170 | 10 provinsi × 18 bulan; satu baris per sel |
| hasil `melt` → `pivot` kembali | 180 | 10 | −170 | kembali ke bentuk lebar semula (`equals` = True) |
| Tabel berlubang 2025-01 → setelah `unstack` dan `melt` | 71 | 80 | +9 | `unstack` memunculkan NaN pada 9 kombinasi tanpa transaksi (10 provinsi × 8 kategori = 80) |
| Setelah `melt` → setelah `dropna` | 80 | 71 | −9 | baris NaN dibuang sehingga kembali sama dengan tabel awal (`equals` = True setelah diurutkan) |
 
## 6. Jawaban Pertanyaan Analisis
 
1. **Lebar → panjang → lebar.** `equals` langsung = True. Yang harus diperhatikan: `reset_index()` sebelum `melt` (agar provinsi menjadi kolom, id_vars) serta urutan indeks dan kolom; pada tabel lengkap ini urutan hasil `pivot` sudah sama karena `pivot` mengurutkan label, sehingga tidak perlu penyesuaian lain. Tanpa `reset_index()`, `melt()` menghasilkan 180 baris tetapi kolom provinsi hilang.
2. **Tabel berlubang.** Baris sebelum 71, sesudah `melt` 80. Agar `equals` kembali True: `dropna` pada kolom nilai, urutkan menurut provinsi dan kategori, dan `reset_index(drop=True)`. Bila sel kosong diisi 0, muncul 9 baris baru yang berarti "tercatat nol" padahal aslinya tidak ada transaksi: informasi tentang kombinasi yang tidak pernah muncul hilang, dan rata-rata atau cacah yang dihitung kemudian ikut berubah.
3. **Tipe.** `pesanan` kembali sebagai `float64`, bukan `int64`, karena `unstack` memunculkan NaN dan `int64` biasa tidak dapat menyimpan NaN. `equals` menuntut tipe sama, sehingga perlu `astype("int64")` setelah `dropna`.
4. **Kapan bolak-balik tidak dapat mengembalikan tabel asal?** Bila sel kosong dipaksa terisi suatu nilai (mis. 0), atau bila `pivot_table` mengagregasi baris-baris yang berbagi pasangan indeks dan kolom: agregasi menghilangkan baris asal dan tidak dapat dibatalkan.
## 7. Keterbatasan
 
- Percobaan 2 dan 3 hanya memakai satu bulan (2025-01, 9 sel kosong); bulan lain dapat memiliki pola sel kosong yang berbeda.
- `equals` sangat ketat, sehingga hasil `False` dapat berasal dari perbedaan kecil (urutan, tipe) yang tidak mengubah isi data.
- Latihan hanya menguji `melt`, `pivot`, dan `unstack`; transformasi dengan agregasi (`pivot_table`) tidak dapat dibalik dan tidak diuji di sini.
- Analisis memakai keluaran acuan Modul 4, bukan hasil Modul 4 saya sendiri.
## 8. Pengungkapan Penggunaan Alat Bantu
 
Asisten berbasis kecerdasan buatan (Claude, Anthropic) digunakan untuk menyusun draf kode Latihan 6.2 dan kerangka laporan ini. Kode dijalankan sendiri pada notebook, dan seluruh angka dalam laporan berasal dari keluaran kode tersebut.