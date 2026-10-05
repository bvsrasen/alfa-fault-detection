"""ALFA uçuş klasörlerini okuyan fonksiyonlar.

Her uçuş `processed/<uçuş adı>/` altında, her ROS topic'i için ayrı bir CSV:
`<uçuş adı>-mavros-nav_info-roll.csv` gibi. CSV'lerde ilk sütun `%time`
(kayıt anı, ns), diğer sütunlar `field.` önekli mesaj alanları.

Arıza etiketi `failure_status-<yüzey>` topic'lerinden geliyor. Bu topic'ler
yalnızca arıza başladıktan sonra yayınlanıyor, yani ilk mesajın zamanı arıza
başlangıcı. Arızasız uçuşlarda bu dosyalar hiç yok.
"""
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

ARIZA_TOPICLERI = ("engines", "aileron", "rudder", "elevator")

# Zaman ekseninin sıfırı; her uçuşta var ve ~20 Hz ile en sık yayınlanan topic
REFERANS_TOPIC = "mavros-nav_info-roll"


@dataclass
class Ucus:
    ad: str
    klasor: Path
    t0_ns: int
    # yüzey -> arıza başlangıcı (s, t0'a göre)
    arizalar: dict = field(default_factory=dict)

    @property
    def ariza_var(self):
        return bool(self.arizalar)

    @property
    def ariza_baslangic(self):
        """İlk arızanın başlangıcı (s); arızasız uçuşta None."""
        return min(self.arizalar.values()) if self.arizalar else None

    @property
    def etiket_yok(self):
        # Veri setinde bir uçuşun arıza zamanı kaydedilmemiş, adı bunu söylüyor
        return self.ad.endswith("no_ground_truth")

    @property
    def tip(self):
        if self.etiket_yok:
            return "etiketsiz"
        if not self.arizalar:
            return "arızasız"
        return "+".join(sorted(self.arizalar))

    def dosya(self, topic):
        return self.klasor / f"{self.ad}-{topic}.csv"

    def topicler(self):
        onek = len(self.ad) + 1
        return sorted(p.stem[onek:] for p in self.klasor.glob("*.csv"))

    def oku(self, topic):
        """Topic'i okur; `t` sütunu t0'dan itibaren saniye.

        `field.` öneki atılıyor, `field.header.stamp` gibi alanlar `header.stamp` olarak kalıyor.
        """
        df = pd.read_csv(self.dosya(topic))
        t_ns = df.pop("%time")
        df.columns = [c.removeprefix("field.") for c in df.columns]
        # ns'yi önce int olarak çıkarıyoruz, float64'te 1e18 civarında hassasiyet kaybı oluyor
        df.insert(0, "t", (t_ns - self.t0_ns) / 1e9)
        return df


def ucus_ac(klasor):
    klasor = Path(klasor)
    ad = klasor.name
    ref = pd.read_csv(klasor / f"{ad}-{REFERANS_TOPIC}.csv", usecols=["%time"])
    t0 = int(ref["%time"].iloc[0])
    ucus = Ucus(ad=ad, klasor=klasor, t0_ns=t0)
    for yuzey in ARIZA_TOPICLERI:
        yol = ucus.dosya(f"failure_status-{yuzey}")
        if yol.exists():
            s = pd.read_csv(yol, usecols=["%time"])
            ucus.arizalar[yuzey] = (int(s["%time"].iloc[0]) - t0) / 1e9
    return ucus


def ucuslari_ac(kok="veri/processed"):
    kok = Path(kok)
    if not kok.is_dir():
        raise FileNotFoundError(f"{kok} yok; önce `python veri_indir.py` çalıştır")
    return [ucus_ac(p) for p in sorted(kok.iterdir()) if p.is_dir()]
