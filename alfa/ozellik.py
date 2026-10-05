"""Hizalanmış tablodan türetilen büyüklükler. Hepsi sadece o anki örneği kullanıyor."""
import numpy as np

G = 9.80665


def turet(df):
    d = df.copy()
    d["V"] = np.sqrt(d["vn"] ** 2 + d["ve"] ** 2 + d["vd"] ** 2)
    d["e_roll"] = d["roll_k"] - d["roll"]
    d["e_pitch"] = d["pitch_k"] - d["pitch"]
    # Koordineli dönüşte beklenen yaw hızı: g tan(roll) / V
    d["donus_r"] = G * np.tan(np.radians(d["roll"])) / np.maximum(d["V"], 5.0)
    d["roll_kare"] = d["roll"] ** 2
    d["hiz_hata"] = d["hiz_hata"] / 100.0  # cm/s -> m/s
    return d
