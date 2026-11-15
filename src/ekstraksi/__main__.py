"""python -m src.ekstraksi  — jalankan tahap 1 saja dan cetak angka serta perintah metrics.json."""
from src.ekstraksi import jalankan, ringkas

if __name__ == "__main__":
    tabel = jalankan()
    for nama, df in tabel.items():
        print(f"{nama:<18} {df['_berkas_raw'].nunique():>2} berkas {len(df):>6} baris {df.shape[1]:>3} kolom")
    r = ringkas(tabel)
    print("\nSalin ke terminal (ganti <nim> dengan NIM Anda):")
    print("python -m src.common.hasil <nim> " + " ".join(f"{k}={v}" for k, v in r.items()))
