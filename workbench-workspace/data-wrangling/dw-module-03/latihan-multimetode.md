 Jawaban Latihan 3.2

1. Banyak tanda per metode (provinsi_tujuan dipetakan sementara: __ penulisan mentah menjadi __ provinsi; df asli tidak diubah, 24.288 baris)

| metode | ongkir | total_bayar |
|---|---|---|
| z-score | 189 | 432 |
| IQR | 4.398 | 3.000 |
| robust z (MAD) | 6.833 | 3.469 |
| IsolationForest (log10 ongkir + log10 total_bayar) | 247 (gabungan dua fitur) | |

2. Tabel kesepakatan (indeks Jaccard)
Lengkapnya di `keluaran/kesepakatan_metode_m03.csv`.

| | z_ongkir | iqr_ongkir | rz_ongkir | z_total | iqr_total | rz_total | iforest |
|---|---|---|---|---|---|---|---|
| z_ongkir | 1 | 0,043 | 0,028 | 0,129 | 0,029 | 0,026 | 0,519 |
| iqr_ongkir | 0,043 | 1 | 0,644 | 0,062 | 0,241 | 0,249 | 0,054 |
| rz_ongkir | 0,028 | 0,644 | 1 | 0,049 | 0,237 | 0,256 | 0,035 |
| z_total | 0,129 | 0,062 | 0,049 | 1 | 0,144 | 0,125 | 0,193 |
| iqr_total | 0,029 | 0,241 | 0,237 | 0,144 | 1 | 0,865 | 0,050 |
| rz_total | 0,026 | 0,249 | 0,256 | 0,125 | 0,865 | 1 | 0,044 |
| iforest | 0,519 | 0,054 | 0,035 | 0,193 | 0,050 | 0,044 | 1 |

Paling sepakat: iqr_total dan rz_total (0,865), lalu iqr_ongkir dan rz_ongkir (0,644).
Paling tidak sepakat: z_ongkir dan rz_ongkir (0,028), serta z_ongkir dan rz_total (0,026).

3. Mengapa metode tidak sepakat
Setiap metode mendefinisikan "jauh" secara berbeda. Z-score memakai rata-rata dan simpangan
baku yang ikut tertarik pencilan, sehingga menandai paling sedikit (189 pada ongkir).
IQR dan robust z memakai kuartil dan median sehingga jauh lebih peka pada data miring
(4.398 dan 6.833). Metode sejenis saling sepakat (iqr_total dan rz_total 0,865), sedangkan
yang berbeda dasar hampir tidak beririsan (z_ongkir dan rz_ongkir 0,028). IsolationForest
menilai dua fitur sekaligus dan paling dekat dengan z_ongkir (0,519), karena keduanya
menangkap nilai yang benar-benar ekstrem; dengan metode kuartil dan median ia hanya 0,035
sampai 0,054. Jumlah tandanya juga ikut ditentukan parameter contamination.

4. Robust z pada ongkir
MAD ongkir bernilai 0 di 15 dari 15 provinsi. Artinya setidaknya separuh ongkir sama persis
dengan median provinsinya (tarif tetap). Rumus 0,6745 × (x − median) / MAD lalu membagi
dengan nol, sehingga setiap ongkir yang sedikit saja berbeda dari median otomatis ditandai.
Seluruh 6.833 tanda robust z pada ongkir berasal dari provinsi ber-MAD 0, sekitar 36 kali
lipat z-score (189), dan irisannya dengan z-score hanya 0,028. Itu artefak rumus, bukan
pencilan sungguhan.

5. Pembelian grosir sah yang ikut ditandai
Grosir didefinisikan sebagai jumlah >= 5 (persentil ke-99), sebanyak 3.135 pembelian
(12,9% dari 24.288 baris; ambang ini longgar karena 90% data sudah <= 5, sedangkan
persentil ke-99,9 bernilai 164,9 dan maksimum 198).
Yang ikut ditandai pada total_bayar: z-score 238 (7,6%), IQR 766 (24,4%),
robust z 889 (28,4%), IsolationForest 225 (7,2%).
Pembelian ini besar tetapi sah, sehingga tanda itu alarm palsu. Metode berbasis
median/kuartil paling banyak salah menandai grosir (IQR dan robust z), z-score
dan IsolationForest paling sedikit.

6. Keputusan
- Robust z tidak dipakai pada ongkir selama MAD = 0 (atau MAD diberi batas bawah);
  ongkir di luar tarif tetap diperiksa dengan aturan lain.
- Tanda pada pembelian grosir tidak dibuang atau dikoreksi; hanya diberi bendera untuk
  ditinjau, karena total_bayar besar tetapi sah.
- Penyeragaman permanen provinsi_tujuan ditunda ke Modul 4; pemetaan di sini hanya untuk analisis.