"""Farklı hızlardaki topic'leri ortak 10 Hz zaman tabanına getirir.

Her ızgara anında, her sinyalin o ana kadar gelmiş son örneği kullanılıyor
(sıfırıncı derece tutma). İnterpolasyon yapmıyoruz çünkü iki örnek arasını
doldurmak bir sonraki örneği, yani gelecekteki veriyi kullanmak demek. Uçuş
bilgisayarında da durum aynı: elimizde son gelen değer var.

10 Hz seçildi çünkü en hızlı gerçek ölçüm (ham IMU, barometre) 10 Hz.
nav_info-* topic'leri 20 Hz yayınlanıyor ama ölçülen yönelim 2,5 Hz'de
değişiyor.
"""
import numpy as np
import pandas as pd

HZ = 10.0
DT = 1.0 / HZ

# sinyal adı -> (topic, alan)
# rc-out ve vfr_hud.throttle bilerek yok: arıza bu çıkışlar kilitlenerek
# uygulanmış, girdi olarak kullanılırsa etiketi okumuş oluruz.
SINYALLER = {
    "p": ("mavros-imu-data_raw", "angular_velocity.x"),
    "q": ("mavros-imu-data_raw", "angular_velocity.y"),
    "r": ("mavros-imu-data_raw", "angular_velocity.z"),
    "ax": ("mavros-imu-data_raw", "linear_acceleration.x"),
    "ay": ("mavros-imu-data_raw", "linear_acceleration.y"),
    "az": ("mavros-imu-data_raw", "linear_acceleration.z"),
    "roll_k": ("mavros-nav_info-roll", "commanded"),
    "roll": ("mavros-nav_info-roll", "measured"),
    "pitch_k": ("mavros-nav_info-pitch", "commanded"),
    "pitch": ("mavros-nav_info-pitch", "measured"),
    "yaw": ("mavros-nav_info-yaw", "measured"),
    "vn": ("mavros-nav_info-velocity", "meas_x"),
    "ve": ("mavros-nav_info-velocity", "meas_y"),
    "vd": ("mavros-nav_info-velocity", "meas_z"),
    "basinc": ("mavros-imu-atm_pressure", "fluid_pressure"),
    # Otopilotun kendi hata terimleri (irtifa m, hava hızı cm/s). Hava hızı hatası
    # otopilotun sentetik hava hızı tahmininden geliyor, sensör 0 iken de dolu.
    "alt_hata": ("mavros-nav_info-errors", "alt_error"),
    "hiz_hata": ("mavros-nav_info-errors", "aspd_error"),
}


def son_ornek(t_kaynak, deger, t_izgara):
    """Her ızgara anı için t <= t_izgara olan son örneği döndürür."""
    i = np.searchsorted(t_kaynak, t_izgara, side="right") - 1
    if (i < 0).any():
        raise ValueError("ızgara, sinyalin ilk örneğinden önce başlıyor")
    return deger[i]


def hizala(ucus, sinyaller=SINYALLER):
    """Uçuşu 10 Hz tabloya çevirir.

    Izgara, bütün sinyallerin en az bir örneği geldikten sonra başlıyor ve
    herhangi bir sinyal bittiğinde bitiyor. `ariza` sütunu, ızgara anında
    arızanın başlamış olup olmadığı (değerlendirme için, yöntemlere girdi değil).
    """
    topicler = {}
    for topic, _ in sinyaller.values():
        if topic not in topicler:
            df = ucus.oku(topic)
            # Kayıt anları nadiren de olsa sıralı gelmeyebiliyor
            topicler[topic] = df.sort_values("t", kind="stable").reset_index(drop=True)

    bas = max(df["t"].iloc[0] for df in topicler.values())
    son = min(df["t"].iloc[-1] for df in topicler.values())
    # Izgarayı DT'nin katlarına oturtuyoruz, uçuşlar arasında karşılaştırma kolay olsun
    t = np.arange(np.ceil(bas / DT), np.floor(son / DT) + 1) * DT

    tablo = pd.DataFrame({"t": t})
    for ad, (topic, alan) in sinyaller.items():
        df = topicler[topic]
        tablo[ad] = son_ornek(df["t"].to_numpy(), df[alan].to_numpy(dtype=float), t)

    tablo["ariza"] = t >= ucus.ariza_baslangic if ucus.ariza_var else False
    return tablo
