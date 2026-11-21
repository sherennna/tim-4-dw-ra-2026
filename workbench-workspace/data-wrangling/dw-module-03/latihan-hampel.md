## Jawaban Latihan 3.1

Tabel lengkap ada di `keluaran/parameter_hampel_m03.csv` (jendela 7, 13, 25; k = 2..10).
Kurva: `keluaran/05_kurva_hampel.png`.

| jendela | k | total | lonjakan 85,0 | jejak pintu | kejadian nyata | lainnya |
|---|---|---|---|---|---|---|
| 7 | 10 | 458 | 41 | 0 | 0 | 417 |
| 13 | 10 | 401 | 42 | 0 | 1 | 358 |
| 25 | 10 | 377 | 42 | 0 | 6 | 329 |

Pilihan: JENDELA_H = 13, K_H = 10

Alasan: Lonjakan 85,0 totalnya 42. Jendela 7 hanya menangkap 41 di semua k
sehingga tidak memenuhi syarat. Jendela 13 dan 25 menangkap 42 dari 42. Di antara
keduanya, jendela 13 dengan k=10 hanya menandai 1 titik kejadian nyata
(jendela 25: 6) dan total tanda lebih sedikit (401 vs 2510 pada k=2).

Apakah k saja cukup? Tidak. Pada jendela 13 dan 25 kolom kejadian nyata tidak
pernah 0 walau k dinaikkan sampai 10. Pada jendela 7 nilainya 0, tetapi satu
lonjakan 85,0 terlewat.

Aturan untuk pintu terbuka: titik yang ditandai Hampel tidak dikoreksi bila
berada di dalam rentang [mulai, selesai] kejadian berjenis pintu atau kejadian
nyata pada tabel kejadian. Koreksi hanya untuk titik yang di luar rentang itu
(termasuk seluruh lonjakan 85,0).