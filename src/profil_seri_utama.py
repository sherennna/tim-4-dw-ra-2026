"""Tahap 2 — Profil statistik deskriptif, grafik, dan deteksi calon anomali seri utama BPS."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.ekstraksi import bps

SERI_UTAMA = {
    "var1393": "Kejadian Malaria per 1.000 Penduduk (2010–2021)",
    "var1480": "Prevalensi Tekanan Darah Tinggi / Hipertensi (%)",
    "var1435": "Prevalensi Merokok Penduduk Usia >= 15 Tahun (%)",
}

DIR_GAMBAR = Path("reports/gambar")
JALUR_LAPORAN = Path("reports/profil-seri-utama.md")
JALUR_CSV_ANOMALI = Path("reports/calon-anomali-seri-utama.csv")


def muat_data_bps() -> pd.DataFrame:
    df = bps.baca_semua().copy()
    df = df[df["seri_kode"].isin(SERI_UTAMA)].copy()
    df["nilai"] = pd.to_numeric(df["nilai"], errors="coerce")
    df["tahun_num"] = pd.to_numeric(df["tahun"], errors="coerce")
    df["wilayah_kode"] = pd.to_numeric(df["wilayah_id"], errors="coerce").astype("Int64")
    df["nama_wilayah"] = df["wilayah"].astype(str).str.strip()
    return df.dropna(subset=["nilai", "tahun_num", "wilayah_kode"]).copy()


def hitung_statistik_seri(df: pd.DataFrame) -> pd.DataFrame:
    baris = []
    for seri, judul in SERI_UTAMA.items():
        sub = df[df["seri_kode"] == seri]["nilai"]
        q1, med, q3 = np.percentile(sub, [25, 50, 75])
        baris.append(
            {
                "seri_kode": seri,
                "indikator": judul,
                "n_obs": int(sub.count()),
                "mean": round(float(sub.mean()), 3),
                "std": round(float(sub.std(ddof=1)), 3),
                "min": round(float(sub.min()), 3),
                "q1": round(float(q1), 3),
                "median": round(float(med), 3),
                "q3": round(float(q3), 3),
                "iqr": round(float(q3 - q1), 3),
                "max": round(float(sub.max()), 3),
            }
        )
    return pd.DataFrame(baris)


def hitung_statistik_provinsi(df: pd.DataFrame) -> pd.DataFrame:
    grp = (
        df.groupby(["seri_kode", "wilayah_kode", "nama_wilayah"], as_index=False)["nilai"]
        .agg(
            n_tahun="count",
            mean="mean",
            std="std",
            min="min",
            q1=lambda s: np.percentile(s, 25),
            median="median",
            q3=lambda s: np.percentile(s, 75),
            max="max",
        )
    )
    for col in ["mean", "std", "min", "q1", "median", "q3", "max"]:
        grp[col] = grp[col].round(3)
    return grp.sort_values(["seri_kode", "wilayah_kode"]).reset_index(drop=True)


def deteksi_calon_anomali(df: pd.DataFrame) -> pd.DataFrame:
    hasil = []
    for seri in SERI_UTAMA:
        sub = df[df["seri_kode"] == seri].copy()
        q1, q3 = np.percentile(sub["nilai"], [25, 75])
        iqr = q3 - q1
        batas_bawah = q1 - 1.5 * iqr
        batas_atas = q3 + 1.5 * iqr
        mean = sub["nilai"].mean()
        std = sub["nilai"].std(ddof=1)
        sub["z_score"] = (sub["nilai"] - mean) / std if std > 0 else 0.0

        for _, r in sub.iterrows():
            alasan = []
            if r["nilai"] > batas_atas:
                alasan.append(f"IQR atas (nilai {r['nilai']:.2f} > {batas_atas:.2f})")
            elif r["nilai"] < batas_bawah:
                alasan.append(f"IQR bawah (nilai {r['nilai']:.2f} < {batas_bawah:.2f})")
            if abs(r["z_score"]) > 2.5:
                alasan.append(f"z-score ekstrem ({r['z_score']:+.2f})")

            if alasan:
                hasil.append(
                    {
                        "seri_kode": seri,
                        "wilayah_kode": int(r["wilayah_kode"]),
                        "nama_wilayah": r["nama_wilayah"],
                        "periode": str(int(r["tahun_num"])),
                        "nilai": round(float(r["nilai"]), 3),
                        "satuan": r["satuan"],
                        "z_score": round(float(r["z_score"]), 3),
                        "alasan": "; ".join(alasan),
                    }
                )
    return pd.DataFrame(hasil).sort_values(["seri_kode", "wilayah_kode", "periode"]).reset_index(drop=True)


def buat_grafik(df: pd.DataFrame) -> list[str]:
    DIR_GAMBAR.mkdir(parents=True, exist_ok=True)
    daftar_berkas = []

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8))
    for ax, (seri, judul) in zip(axes, SERI_UTAMA.items()):
        sub = df[df["seri_kode"] == seri]
        ax.boxplot(sub["nilai"].dropna(), vert=True, patch_artist=True, boxprops=dict(facecolor="#4C78A8", alpha=0.7))
        ax.set_title(f"{seri}\n({sub['satuan'].iloc[0]})", fontsize=10)
        ax.set_xticks([1])
        ax.set_xticklabels([seri])
        ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.suptitle("Sebaran Nilai & Outlier Seri Utama BPS (Kasus 04)", fontsize=12, fontweight="bold")
    fig.tight_layout()
    p_box = DIR_GAMBAR / "boxplot_seri_utama_bps.png"
    fig.savefig(p_box, dpi=150)
    plt.close(fig)
    daftar_berkas.append(str(p_box).replace("\\", "/"))

    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=False)
    for ax, (seri, judul) in zip(axes, SERI_UTAMA.items()):
        sub = df[df["seri_kode"] == seri].copy()
        nas = sub[sub["wilayah_kode"] == 9999].sort_values("tahun_num")
        prov = sub[sub["wilayah_kode"] != 9999]

        for _, g in prov.groupby("wilayah_kode"):
            g = g.sort_values("tahun_num")
            ax.plot(g["tahun_num"], g["nilai"], color="#B0B0B0", alpha=0.35, linewidth=0.9)

        if not nas.empty:
            ax.plot(nas["tahun_num"], nas["nilai"], color="#1F77B4", marker="o", linewidth=2.3, label="Nasional (9999)")

        top_prov = (
            prov.groupby(["wilayah_kode", "nama_wilayah"])["nilai"]
            .max()
            .sort_values(ascending=False)
            .head(2)
            .index.tolist()
        )
        warna_sorot = ["#D62728", "#FF7F0E"]
        for (wk, nm), wrn in zip(top_prov, warna_sorot):
            gp = prov[prov["wilayah_kode"] == wk].sort_values("tahun_num")
            ax.plot(gp["tahun_num"], gp["nilai"], color=wrn, marker="s", linewidth=1.7, label=f"{nm} ({wk})")

        ax.set_title(f"{seri} — {judul}", fontsize=10, fontweight="bold")
        ax.set_ylabel(sub["satuan"].iloc[0], fontsize=9)
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend(loc="best", fontsize=8)

    fig.tight_layout()
    p_ts = DIR_GAMBAR / "deret_waktu_seri_utama_bps.png"
    fig.savefig(p_ts, dpi=150)
    plt.close(fig)
    daftar_berkas.append(str(p_ts).replace("\\", "/"))

    return daftar_berkas


def tulis_laporan(df: pd.DataFrame, stat_seri: pd.DataFrame, stat_prov: pd.DataFrame, anomali: pd.DataFrame, gambar: list[str]) -> None:
    JALUR_LAPORAN.parent.mkdir(parents=True, exist_ok=True)
    anomali.to_csv(JALUR_CSV_ANOMALI, index=False)

    lines = [
        "# Profil Statistik & Calon Anomali Seri Utama BPS (Kasus 04)",
        "",
        "Dokumen ini merangkum hasil eksplorasi **Tahap 2** untuk tiga seri utama BPS pada Kasus 04: `var1393` (kejadian malaria), `var1480` (prevalensi tekanan darah tinggi), dan `var1435` (prevalensi merokok). Deteksi dilakukan untuk **menandai** calon anomali menggunakan metode **IQR** (`< Q1 - 1.5×IQR` atau `> Q3 + 1.5×IQR`) dan **z-score** (`|z| > 2.5`) tanpa menghapus maupun mengubah nilai asli.",
        "",
        "## 1. Statistik Deskriptif per Seri",
        "",
        stat_seri.to_markdown(index=False),
        "",
        "## 2. Visualisasi Sebaran & Deret Waktu",
        "",
        f"- **Boxplot Sebaran Nilai:** `{gambar[0]}`",
        f"- **Deret Waktu Nasional & Provinsi:** `{gambar[1]}`",
        "",
        f"![Boxplot Seri Utama BPS](gambar/{Path(gambar[0]).name})",
        "",
        f"![Deret Waktu Seri Utama BPS](gambar/{Path(gambar[1]).name})",
        "",
        "## 3. Daftar Calon Anomali Terdeteksi",
        "",
        f"Total terdeteksi **{len(anomali)}** observasi calon anomali (daftar lengkap juga tersimpan di `{JALUR_CSV_ANOMALI.as_posix()}`).",
        "",
        anomali.to_markdown(index=False) if not anomali.empty else "_Tidak ada calon anomali terdeteksi._",
        "",
        "## 4. Ringkasan Statistik Deskriptif per Provinsi (Semua Seri Utama)",
        "",
        stat_prov.to_markdown(index=False),
        "",
    ]
    JALUR_LAPORAN.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    df = muat_data_bps()
    stat_seri = hitung_statistik_seri(df)
    stat_prov = hitung_statistik_provinsi(df)
    anomali = deteksi_calon_anomali(df)
    gambar = buat_grafik(df)
    tulis_laporan(df, stat_seri, stat_prov, anomali, gambar)
    print(f"Profil seri utama selesai: {len(df)} observasi, {len(anomali)} calon anomali, grafik={gambar}")


if __name__ == "__main__":
    main()
