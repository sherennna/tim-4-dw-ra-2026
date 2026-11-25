# Kelengkapan panel provinsi x tahun (BPS)

Mode sel tidak berlaku: hukum. Sel berlaku = 38 provinsi dikurangi provinsi yang belum berdiri/terbit pada tahun itu. Persen terisi = sel terisi / sel berlaku. Baris Indonesia (9999) dilaporkan terpisah.

## var1393

| tahun | sel berlaku | terisi | missing | tidak berlaku | persen terisi | ada baris Indonesia |
|---|---|---|---|---|---|---|
| 2010 | 33 | 33 | 0 | 5 | 100.0 | ya |
| 2011 | 33 | 33 | 0 | 5 | 100.0 | ya |
| 2012 | 34 | 33 | 1 | 4 | 97.1 | ya |
| 2013 | 34 | 33 | 1 | 4 | 97.1 | ya |
| 2014 | 34 | 34 | 0 | 4 | 100.0 | ya |
| 2015 | 34 | 34 | 0 | 4 | 100.0 | ya |
| 2016 | 34 | 34 | 0 | 4 | 100.0 | ya |
| 2017 | 34 | 34 | 0 | 4 | 100.0 | ya |
| 2018 | 34 | 34 | 0 | 4 | 100.0 | ya |
| 2019 | 34 | 34 | 0 | 4 | 100.0 | ya |
| 2020 | 34 | 34 | 0 | 4 | 100.0 | ya |
| 2021 | 34 | 34 | 0 | 4 | 100.0 | ya |

## var1435

| tahun | sel berlaku | terisi | missing | tidak berlaku | persen terisi | ada baris Indonesia |
|---|---|---|---|---|---|---|
| 2015 | 34 | 34 | 0 | 4 | 100.0 | ya |
| 2016 | 34 | 34 | 0 | 4 | 100.0 | ya |
| 2017 | 34 | 34 | 0 | 4 | 100.0 | ya |
| 2018 | 34 | 34 | 0 | 4 | 100.0 | ya |
| 2019 | 34 | 34 | 0 | 4 | 100.0 | ya |
| 2020 | 34 | 34 | 0 | 4 | 100.0 | ya |
| 2021 | 34 | 34 | 0 | 4 | 100.0 | ya |
| 2022 | 38 | 34 | 4 | 0 | 89.5 | ya |
| 2023 | 38 | 34 | 4 | 0 | 89.5 | ya |
| 2024 | 38 | 38 | 0 | 0 | 100.0 | ya |
| 2025 | 38 | 38 | 0 | 0 | 100.0 | ya |

## var1480

| tahun | sel berlaku | terisi | missing | tidak berlaku | persen terisi | ada baris Indonesia |
|---|---|---|---|---|---|---|
| 2007 | 33 | 33 | 0 | 5 | 100.0 | ya |
| 2013 | 34 | 33 | 1 | 4 | 97.1 | ya |
| 2016 | 34 | 0 | 34 | 4 | 0.0 | ya |
| 2018 | 34 | 34 | 0 | 4 | 100.0 | ya |

## Rentang tahun per seri

| seri | tahun awal | tahun akhir | jumlah tahun |
|---|---|---|---|
| var1393 | 2010 | 2021 | 12 |
| var1435 | 2015 | 2025 | 11 |
| var1480 | 2007 | 2018 | 3 |

## Ringkasan Sebelum vs Sesudah Aturan Sel (Tahap 4 - Gold)

- **Sebelum aturan sel:** Grid provinsi x periode awal masih mencakup kombinasi wilayah/tahun yang belum terbit atau belum berdiri secara hukum pada tahun observasi, serta berpotensi memuat duplikasi/ketidakselarasan sebelum aturan satu nilai per sel (#20) diterapkan.
- **Sesudah aturan sel (mode hukum + jendela bersama 2015-2021):** Sel yang di luar masa berlakunya wilayah/seri diklasifikasikan sebagai **belum terbit**, celah observasi (*gap*) **tidak diisi** tanpa keputusan tertulis dan dirujuk ke `log-keputusan.csv`, sedangkan titik diskontinuitas/perubahan seri ditandai sebagai **patahan** (*break*).

| seri | rentang data seri | jendela analisis bersama | perlakuan sel kosong (gap) | penanda kondisi sel |
|---|---|---|---|---|
| var1393 | 2010-2021 | 2015-2021 | tidak diisi tanpa keputusan tertulis | celah, belum terbit, patahan |
| var1480 | 2007-2018 | 2015-2021 (titik survei 2018; 2016 nasional) | tidak diisi tanpa keputusan tertulis | celah, belum terbit, patahan |
| var1435 | 2015-2025 | 2015-2021 (cakupan penuh s.d. 2025) | tidak diisi tanpa keputusan tertulis | celah, belum terbit, patahan |
