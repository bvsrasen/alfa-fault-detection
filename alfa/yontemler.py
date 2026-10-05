"""Karşılaştırılan iki tespit yöntemi: takip hatası eşiği (Esik) ve
fiziksel artıklar üzerinde lojistik regresyon (Lojistik).

İkisinin arayüzü aynı: `egit(egitim)` eğitim uçuşlarıyla parametreleri
ayarlar, `skor(df)` hizalanmış bir uçuş için örnek başına skor döndürür.
Eşik seçimi degerlendirme.py'de, iki yöntem için de aynı kuralla.

Eğitimde "nominal" örnek: ısınma süresinden sonra ve arıza başlamadan önce.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from alfa import degerlendirme as de
from alfa.ozellik import turet

# Artık kanalları: hedef sinyal -> onu açıklayan büyüklükler.
# Her biri basit bir fiziksel ilişki, katsayılar nominal uçuştan en küçük
# kareler ile bulunuyor.
KANALLAR = {
    # İleri ivme: otopilot uçak alçakta ya da yavaşken gazı açıyor. İvmeölçer
    # yerçekiminin gövde eksenindeki payını da ölçtüğü için burun yukarıdayken
    # okunan değer artıyor. Motor durunca ölçülen ivme beklentinin altında kalıyor.
    "ax": ["alt_hata", "hiz_hata", "pitch"],
    # Düzgün uçuşta yanal ivme sıfıra yakın; takılı rudder bunu bozuyor.
    "ay": [],
    # Roll hızı roll takip hatasıyla orantılı olmalı (aileron).
    "p": ["e_roll"],
    # Pitch hızı pitch takip hatasıyla ve dönüşte roll ile ilişkili (elevator).
    "q": ["e_pitch", "roll_kare"],
    # Koordineli dönüşte yaw hızı g tan(roll) / V.
    "r": ["donus_r"],
}


def nominal(d, ariza_s):
    m = d["t"].to_numpy() >= de.ISINMA_S
    if ariza_s is not None:
        m &= d["t"].to_numpy() < ariza_s
    return m


def tasarim_matrisi(d, girdiler):
    return np.column_stack([np.ones(len(d))] + [d[g].to_numpy() for g in girdiler])


def kalici_min(x, n):
    """Son n örneğin en küçüğü; skorun n örnek boyunca yüksek kalmasını şart koşar."""
    return pd.Series(x).rolling(n, min_periods=n).min().fillna(-np.inf).to_numpy().copy()


class ArtikModeli:
    """KANALLAR'daki doğrusal modeller ve nominal artık standart sapmaları."""

    def __init__(self, kanallar=KANALLAR):
        self.kanallar = kanallar

    def egit(self, egitim):
        tablolar = [turet(d)[nominal(d, u.ariza_baslangic)] for u, d in egitim]
        nom = pd.concat(tablolar)
        self.w, self.sigma = {}, {}
        for hedef, girdiler in self.kanallar.items():
            X = tasarim_matrisi(nom, girdiler)
            w, *_ = np.linalg.lstsq(X, nom[hedef].to_numpy(), rcond=None)
            self.w[hedef] = w
            self.sigma[hedef] = np.std(nom[hedef].to_numpy() - X @ w)
        return self

    def z(self, d):
        """Normalize artıklar, (örnek, kanal) boyutunda."""
        d = turet(d)
        return np.column_stack([
            (d[h].to_numpy() - tasarim_matrisi(d, g) @ self.w[h]) / self.sigma[h]
            for h, g in self.kanallar.items()
        ])


class Esik:
    """Referans: roll ve pitch takip hatasına doğrudan eşik.

    Skor, iki hatanın nominal standart sapmaya bölünmüş büyüğü; tek örneklik
    sıçramalar alarm vermesin diye son `n` örnek boyunca en küçük değeri.
    """

    def __init__(self, n=5):
        self.n = n

    def egit(self, egitim):
        nom = pd.concat([turet(d)[nominal(d, u.ariza_baslangic)] for u, d in egitim])
        self.s_roll = nom["e_roll"].std()
        self.s_pitch = nom["e_pitch"].std()
        return self

    def skor(self, d):
        d = turet(d)
        anlik = np.maximum(np.abs(d["e_roll"]) / self.s_roll, np.abs(d["e_pitch"]) / self.s_pitch)
        return kalici_min(anlik.to_numpy(), self.n)


class Lojistik:
    """Normalize artıklar ve kısa pencere istatistikleri üzerinde lojistik
    regresyon. Etiket: arıza başladıktan sonraki örnekler 1, öncekiler 0.

    Öznitelikler (hepsi nedensel), KANALLAR'daki her artık için: anlık
    değer, mutlak değer, 1 s ve 3 s ortalaması, 1 s standart sapması.
    5 artık x 5 = 25 öznitelik.

    logit = b + sum(w_i * x_i); büyüdükçe arıza olasılığı artıyor. Skor,
    logit'in son `n` örnekteki en küçüğü: alarm için logit'in `n` örnek
    boyunca yüksek kalması gerekiyor.
    """

    def __init__(self, n=5, C=0.1):
        self.n = n
        self.C = C  # düzenlileştirme: küçüldükçe ağırlıklar sıfıra yakın tutuluyor
        self.model = ArtikModeli()

    def ozellikler(self, d):
        z = pd.DataFrame(self.model.z(d))
        parcalar = [z, z.abs(),
                    z.rolling(10, min_periods=1).mean(),
                    z.rolling(30, min_periods=1).mean(),
                    z.rolling(10, min_periods=2).std().fillna(0.0)]
        return np.column_stack([p.to_numpy() for p in parcalar])

    def egit(self, egitim):
        self.model.egit(egitim)
        X, y = [], []
        for _, d in egitim:
            m = d["t"].to_numpy() >= de.ISINMA_S
            X.append(self.ozellikler(d)[m])
            y.append(d["ariza"].to_numpy(dtype=bool)[m])
        X, y = np.vstack(X), np.concatenate(y)
        # Öznitelikleri aynı ölçeğe getiriyoruz; böylece ağırlıklar karşılaştırılabilir
        self.ort = X.mean(axis=0)
        self.ss = X.std(axis=0)
        # Arızalı örnekler azınlıkta; "balanced" iki sınıfa eşit önem veriyor
        self.lr = LogisticRegression(C=self.C, class_weight="balanced", max_iter=5000)
        self.lr.fit((X - self.ort) / self.ss, y)
        return self

    def logit(self, d):
        X = (self.ozellikler(d) - self.ort) / self.ss
        return X @ self.lr.coef_[0] + self.lr.intercept_[0]

    def skor(self, d):
        s = kalici_min(self.logit(d), self.n)
        s[d["t"].to_numpy() < de.ISINMA_S] = -np.inf
        return s
