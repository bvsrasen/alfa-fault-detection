"""Eğitilmiş modeli C'ye aktarır (c/alfa_param.c) ve C kodunu çalıştırır.

C tarafı özniteliklerin ortalamasını çıkarıp standart sapmaya bölmüyor; bu
ölçekleme önceden ağırlıklara katılıyor:
    sum(w * (x - m) / s) + b  =  sum((w / s) * x) + (b - sum(w * m / s))
"""
import subprocess
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

from alfa import degerlendirme as de

C_KLASOR = Path(__file__).resolve().parent.parent / "c"
CLI = C_KLASOR / "build" / "alfa_cli"

# alfa_girdi_t sırası
GIRDI_SUTUNLARI = ["t", "p", "q", "r", "ax", "ay", "roll_k", "roll", "pitch_k", "pitch",
                   "vn", "ve", "vd", "alt_hata", "hiz_hata"]
# C'de sabit kodlu kanal yapısı; Python tarafında değişirse burası uyarsın
C_KANALLARI = {
    "ax": ["alt_hata", "hiz_hata", "pitch"],
    "ay": [],
    "p": ["e_roll"],
    "q": ["e_pitch", "roll_kare"],
    "r": ["donus_r"],
}


def parametreler(lojistik, esik):
    """Eğitilmiş Lojistik nesnesinden alfa_param_t alanları, C'deki sırayla."""
    if lojistik.model.kanallar != C_KANALLARI or lojistik.n != 5:
        raise ValueError("model yapısı C koduyla uyuşmuyor")
    w = lojistik.lr.coef_[0] / lojistik.ss
    b = lojistik.lr.intercept_[0] - np.sum(lojistik.lr.coef_[0] * lojistik.ort / lojistik.ss)
    m = lojistik.model
    return {
        "w_ax": list(m.w["ax"]),
        "w_ay": list(m.w["ay"]),
        "w_p": list(m.w["p"]),
        "w_q": list(m.w["q"]),
        "w_r": list(m.w["r"]),
        "sigma": [m.sigma[k] for k in C_KANALLARI],
        "lr_w": list(w),
        "lr_b": b,
        "esik": esik,
        "isinma_s": de.ISINMA_S,
    }


def c_float(x):
    """float32'yi tam temsil eden C sabiti: 0.1f, 5.0f, 1e-05f."""
    s = f"{float(x):.9g}"
    if not any(c in s for c in ".e"):
        s += ".0"
    return s + "f"


def kaynak_yaz(prm, yol, aciklama=""):
    """MCU'ya gömülecek alfa_param.c dosyası."""
    alanlar = []
    for ad, deger in prm.items():
        if isinstance(deger, list):
            alanlar.append(f"    .{ad} = {{ {', '.join(c_float(v) for v in deger)} }},")
        else:
            alanlar.append(f"    .{ad} = {c_float(deger)},")
    metin = (
        "/* Bu dosya c_dogrula.py tarafından üretildi, elle değiştirmeyin. */\n"
        + (f"/* {aciklama} */\n" if aciklama else "")
        + '#include "alfa_tespit.h"\n\n'
        + "const alfa_param_t ALFA_PARAM = {\n" + "\n".join(alanlar) + "\n};\n"
    )
    Path(yol).write_text(metin)


def derle():
    subprocess.run(["make", "-s", "-C", str(C_KLASOR)], check=True)


def calistir(d):
    """Hizalanmış uçuşu C dedektöründen geçirir; t, logit, skor, alarm döner."""
    girdi = d[GIRDI_SUTUNLARI].to_csv(index=False, float_format="%.9g")
    cikti = subprocess.run([str(CLI)], input=girdi, capture_output=True, text=True, check=True).stdout
    return pd.read_csv(StringIO(cikti))
