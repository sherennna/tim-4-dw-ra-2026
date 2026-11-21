from src.validasi import JALUR_SILVER_DEFAULT, _contoh_uji_sintetis, jalankan, validasi_silver

if __name__ == "__main__":
    if JALUR_SILVER_DEFAULT.exists():
        jalankan()
    else:
        print("Info: data/silver/silver.parquet belum ada di branch ini; menjalankan uji mandiri skema validasi...")
        hasil = validasi_silver(_contoh_uji_sintetis())
        print(
            f"Uji mandiri LOLOS: {hasil['aturan_lolos']}/{hasil['aturan_validasi']} aturan, "
            f"outlier_malaria={hasil['baris_outlier_malaria']}, proyeksi_who={hasil['baris_proyeksi_who']}"
        )