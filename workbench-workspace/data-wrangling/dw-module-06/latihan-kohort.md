# Laporan Modul 06 — Latihan 6.1: Kohort Pelanggan dan Retensi
| Komponen | Isi |
|---|---|
| Nama | Talitha Justine |
| NIM | 124450076 |
| Tanggal pengumpulan | 04 November 2026 |
| Seed dan ukuran data | seed 2026, ukuran kecil |
| Versi Python dan pandas | |

## 1. Ringkasan

Latihan ini membentuk kohort pelanggan dari pesanan selesai berdasarkan id_entitas dan mengukur retensinya per bulan. Retensi bulan ke-1 tertimbang adalah 13,58%, sedikit di bawah rata-rata sederhana antarkohort (14,00%). Keputusan terpentingnya: 213 pesanan pembeli tamu dikeluarkan dari kohort karena tidak punya identitas yang dapat dilacak; sel kohort yang belum teramati dibiarkan kosong, bukan 0, karena mengisi 0 menurunkan retensi bulan ke-6 dari 13,64% menjadi 9,10% secara semu; dan retensi dilaporkan sebagai jumlah pembilang dibagi jumlah penyebut. Memakai id_pelanggan menggelembungkan ukuran kohort (5.099 vs 4.491) dan menurunkan retensi bulan ke-1 menjadi 12,28%, karena satu orang yang memakai web dan aplikasi terhitung dua pelanggan.

## 2. Data yang Dipakai

1. data/acuan/transaksi_m04.parquet: 24.000 baris × 46 kolom (15.744 pesanan).
2. data/acuan/produk_m04.parquet: 850 baris × 15 kolom; data/acuan/pelanggan_m04.parquet: 5.760 baris × 18 kolom (keluaran acuan Modul 4).
3. Tabel turunan Bagian A–D: pesanan_m06 (15.744 baris) dan selesai (12.985 pesanan selesai berwaktu sah, omzet Rp8.024,2 juta).
4. Latihan ini memakai selesai, Januari 2025 sampai Juni 2026 (18 bulan), dengan kunci id_entitas, dan id_pelanggan untuk perbandingan pada butir 4.

## 3. Temuan dan Bukti

1. **Pembeli tamu** (sel TODO 1). 213 pesanan selesai (Rp147,2 juta) tidak punya `id_entitas`. `groupby` membuang kunci kosong, jadi pesanan ini tidak masuk kohort, tetapi tetap ada di omzet. Ukuran kohort total 4.491 entitas dalam 18 kohort (bulan pesanan selesai pertama, Januari 2025 sampai Juni 2026); `assert` memastikan jumlah ukuran kohort sama dengan banyak `id_entitas` unik.
2. **Bentuk lebar dan sel kosong** (sel TODO 2). Tabel lebar berukuran 18 kohort × 18 bulan ke-n = 324 sel; 153 sel belum teramati (NaN), 171 sel teramati. Sel yang sudah teramati tetapi tidak ada pelanggan kembali bernilai 0, sedangkan segitiga kanan bawah dibiarkan NaN. `keluaran/kohort_m06.csv` berisi 171 baris (satu baris per sel teramati), dan peta panas retensi disimpan di `keluaran/05_kohort.png`.
   Cuplikan tabel retensi (%; 5 kohort pertama, bulan ke-0 sampai ke-6):
```
   [isi: tempel output sel notebook:  print((R_e.iloc[:5, :7] * 100).round(1).to_string())]
```
3. **Retensi bulan ke-1** (sel TODO 3), 17 kohort teramati (kohort Juni 2026 belum punya bulan ke-1): rata-rata sederhana 14,00%; tertimbang 13,58%.
4. **Retensi bulan ke-6**, 12 kohort teramati: sel kosong dibiarkan 13,64%; sel kosong diisi 0 menjadi 9,10% (dirata-rata atas 18 kohort).
5. **Kunci `id_pelanggan`** (sel TODO 4): ukuran kohort total 5.099 (vs 4.491 dengan `id_entitas`); retensi bulan ke-1 tertimbang 12,28%, lebih rendah daripada 13,58%.

## 4. Keputusan

Keputusan dicatat di `log-keputusan.csv`: K-06-009 (kohort dan pembeli tamu) dan K-06-011 (kunci `id_pelanggan` vs `id_entitas`).
 
| Keputusan | Alternatif yang dipertimbangkan | Mengapa tidak dipilih |
|---|---|---|
| Pembeli tamu (213 pesanan) dikeluarkan dari kohort | Semua pembeli tamu dijadikan satu "pelanggan" | Pembeli tamu bukan satu orang; satu kohort palsu akan menggelembungkan retensi dan ukuran kohort |
| Sel belum teramati dibiarkan NaN dan tidak ditulis ke CSV | Mengisinya dengan 0 | 0 berarti "sudah teramati, tidak ada yang kembali"; mengisi 0 menurunkan retensi bulan ke-6 secara semu (13,64% menjadi 9,10%) |
| Retensi dilaporkan tertimbang | Rata-rata sederhana antarkohort | Memberi bobot sama pada kohort kecil dan besar; aturan modul: rasio = jumlah pembilang / jumlah penyebut |
| Kohort memakai `id_entitas` | `id_pelanggan` | Satu orang di web dan aplikasi terhitung dua pelanggan (5.099 vs 4.491 pelanggan) |
 
## 5. Rekonsiliasi Jumlah Baris
 
| Langkah | Baris sebelum | Baris sesudah | Selisih | Penjelasan |
|---|---:|---:|---:|---|
| transaksi_m04 → tabel pesanan | 24.000 | 15.744 | −8.256 | baris pesanan digabung menjadi satu baris per pesanan (A.4); tidak ada pesanan hilang |
| pesanan → pesanan selesai berwaktu sah (`selesai`) | 15.744 | 12.985 | −2.759 | hanya status selesai dan waktu sah (definisi omzet, B.1) |
| selesai → pesanan pembeli terdaftar | 12.985 | 12.772 | −213 | 213 pesanan pembeli tamu (`id_entitas` kosong) dikeluarkan dari kohort |
| pesanan pembeli terdaftar → pelanggan unik (`ukuran_e`) | 12.772 | 4.491 | −8.281 | pesanan digabung menjadi satu entitas per pelanggan; satuan berubah dari pesanan ke pelanggan |
| kisi kohort × bulan ke-n → `kohort_m06.csv` | 324 | 171 | −153 | 153 sel belum teramati (NaN) tidak ditulis; sel teramati tanpa pelanggan kembali ditulis sebagai 0 |
 
## 6. Jawaban Pertanyaan Analisis
 
1. **Pembeli tamu diapakan, dan berapa pesanannya?** Dikeluarkan dari tabel kohort karena tidak dapat dilacak antarbulan; jumlahnya 213 pesanan selesai (Rp147,2 juta). Pesanan itu tetap ada di omzet.
2. **Apakah sel kosong di kanan bawah 0?** Bukan. Kohort itu belum punya cukup bulan untuk diamati (data berakhir Juni 2026), sehingga nilainya tidak diketahui, bukan nol. Ada 153 sel seperti itu dari 324 sel. Sel yang sudah teramati tetapi tidak ada pelanggan kembali bernilai 0.
3. **Mengapa dua cara menghitung retensi bulan ke-1 berbeda, dan mana yang dilaporkan?** Rata-rata sederhana (14,00%) memberi bobot sama pada setiap kohort, sedangkan cara tertimbang (13,58%) adalah jumlah pelanggan kembali dibagi jumlah ukuran kohort, sehingga kohort besar berbobot lebih besar. Karena angka tertimbang lebih rendah, kohort besar rata-rata punya retensi sedikit di bawah kohort kecil. Yang dilaporkan: tertimbang. Pada bulan ke-6, rata-rata dengan sel kosong dibiarkan adalah 13,64% (12 kohort teramati). Bila sel kosong diisi 0, angkanya turun menjadi 9,10% karena enam kohort yang belum teramati ikut dihitung sebagai "tidak kembali".
4. **id_pelanggan vs id_entitas.** Ukuran kohort total 5.099 vs 4.491, dan retensi bulan ke-1 12,28% vs 13,58%. Satu orang yang memakai web dan aplikasi memiliki dua `id_pelanggan`, sehingga terhitung sebagai dua pelanggan baru, dan belanja lintas kanal tidak terbaca sebagai pelanggan yang kembali. Akibatnya penyebut membesar dan retensi tampak lebih rendah.
## 7. Keterbatasan
 
- Data hanya 18 bulan: retensi bulan ke-1 dihitung dari 17 kohort dan bulan ke-6 hanya dari 12 kohort, sehingga bulan ke-n yang lebih besar bertumpu pada sedikit kohort.
- Retensi mengukur pesanan selesai; pelanggan yang pesanannya dibatalkan atau dikembalikan tidak terhitung sebagai kembali.
- Pembeli tamu (213 pesanan) tidak dapat dianalisis dalam kohort sehingga retensi hanya berlaku untuk pembeli terdaftar.
- Analisis memakai keluaran acuan Modul 4, bukan hasil Modul 4 saya sendiri.
## 8. Pengungkapan Penggunaan Alat Bantu
 
Asisten berbasis kecerdasan buatan (Claude, Anthropic) digunakan untuk menyusun draf kode Latihan 6.1 dan kerangka laporan ini. Kode dijalankan sendiri pada notebook, dan seluruh angka dalam laporan berasal dari keluaran kode tersebut.