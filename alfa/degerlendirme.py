"""ALFA makalesindeki metrikler ve kayıt bazlı çapraz doğrulama.

Metrikler uçuş (sequence) bazında, Keipour vd. (2021) Bölüm 4'teki gibi:
- arızadan önce (ya da arızasız uçuşta) verilen tek bir alarm bile o uçuşu
  yanlış pozitif yapar,
- arızalı uçuşta alarm yalnızca arızadan sonra geldiyse doğru pozitif,
- arızalı uçuşta hiç alarm yoksa yanlış negatif, arızasız uçuşta yoksa doğru negatif.
Tespit süresi = ilk alarm - arıza başlangıcı, sadece doğru pozitiflerde.

Bir yöntem uçuş başına bir `skor` dizisi üretiyor; alarm, skorun eşiği
aştığı ilk an. Eşik, eğitim uçuşlarında doğruluğu en büyük yapan değer
(bkz. esik_sec).
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from alfa.veri import kayit_adi
from alfa.zaman import DT

# Kayıtlar otonom moda geçişle başlıyor: uçak ~23 m/s ile geliyor, otopilot
# ilk ~15 s'de hızı 12-13 m/s'ye indiriyor, arada 45°'lik roll komutları var.
# Bu sürede alarm verilmiyor ve bu örnekler eğitime de girmiyor. En erken
# arıza 49,1 s'de başladığı için hiçbir arızayı örtmüyor.
ISINMA_S = 15.0


@dataclass
class Sonuc:
    ucus: str
    tip: str
    ariza_s: float | None
    alarm_s: float | None
    nominal_s: float = 0.0  # ısınmadan sonra, arızadan önce geçen süre

    @property
    def durum(self):
        if self.ariza_s is None:
            return "DN" if self.alarm_s is None else "YP"
        if self.alarm_s is None:
            return "YN"
        return "DP" if self.alarm_s >= self.ariza_s else "YP"

    @property
    def gecikme(self):
        return self.alarm_s - self.ariza_s if self.durum == "DP" else None


def ilk_alarm(t, skor, esik):
    i = np.flatnonzero((skor > esik) & (t >= ISINMA_S))
    return float(t[i[0]]) if len(i) else None


def nominal_maks(t, skor, ariza_s):
    """Arıza öncesindeki (ısınma sonrası) en büyük skor."""
    m = t >= ISINMA_S
    if ariza_s is not None:
        m &= t < ariza_s
    return float(np.max(skor[m])) if m.any() else -np.inf


def arizadan_sonra_maks(t, skor, ariza_s):
    if ariza_s is None:
        return -np.inf
    m = (t >= ISINMA_S) & (t >= ariza_s)
    return float(np.max(skor[m])) if m.any() else -np.inf


def esik_sec(egitim_skorlari):
    """Eğitim uçuşlarında doğruluğu en büyük yapan eşik.

    egitim_skorlari: [(nominal_maks, arizadan_sonra_maks, arizali_mi), ...]
    Bir uçuş, eşik h için: nominal_maks > h ise YP; değilse arızalıysa ve
    arızadan sonra skor h'yi geçiyorsa DP, geçmiyorsa YN; arızasızsa DN.

    Doğruluk eşiğe göre basamak fonksiyonu; en iyi doğruluğu veren ilk
    aralığın ortası seçiliyor. Aralığın alt ucuna yapışık bir eşik,
    eğitimde en yüksek nominal skoru veren uçuşa göre ayarlanmış olur.
    """
    nom = np.array([a for a, _, _ in egitim_skorlari])
    son = np.array([b for _, b, _ in egitim_skorlari])
    arizali = np.array([c for _, _, c in egitim_skorlari])
    adaylar = np.unique(np.concatenate([nom, son]))
    adaylar = adaylar[np.isfinite(adaylar)]
    if len(adaylar) == 0:
        raise ValueError("eşik seçmek için sonlu skor yok")

    def dogruluk(h):
        yp = nom > h
        dp = ~yp & arizali & (son > h)
        dn = ~yp & ~arizali
        return (dp.sum() + dn.sum()) / len(nom)

    puan = np.array([dogruluk(h) for h in adaylar])
    i = int(np.argmax(puan))
    # adaylar[i] ile bir sonraki aday arasında doğruluk sabit
    ust = adaylar[i + 1] if i + 1 < len(adaylar) else adaylar[i] + 1.0
    return 0.5 * (adaylar[i] + ust)


def metrikler(sonuclar):
    durumlar = [s.durum for s in sonuclar]
    dp, yp, yn, dn = (durumlar.count(k) for k in ("DP", "YP", "YN", "DN"))
    arizali = sum(s.ariza_s is not None for s in sonuclar)
    gec = [s.gecikme for s in sonuclar if s.durum == "DP"]
    saat = sum(s.nominal_s for s in sonuclar) / 3600.0
    return {
        "uçuş": len(sonuclar),
        "DP": dp, "YP": yp, "YN": yn, "DN": dn,
        "doğruluk": (dp + dn) / len(sonuclar),
        "kesinlik": dp / (dp + yp) if dp + yp else float("nan"),
        "duyarlılık": dp / arizali if arizali else float("nan"),
        "ort_tespit_s": float(np.mean(gec)) if gec else float("nan"),
        "maks_tespit_s": float(np.max(gec)) if gec else float("nan"),
        "YP_saat": yp / saat if saat else float("nan"),
    }


def egitim_ozeti(yontem, ucus, d):
    t, s = d["t"].to_numpy(), yontem.skor(d)
    return (nominal_maks(t, s, ucus.ariza_baslangic),
            arizadan_sonra_maks(t, s, ucus.ariza_baslangic), ucus.ariza_var)


def capraz_dogrula(yontem_sinifi, veri, **ayar):
    """Bir kaydı dışarıda bırakarak (leave-one-recording-out) değerlendirir.

    Her katta yöntem kalan kayıtlarla eğitiliyor, eşik de yine yalnızca
    eğitim uçuşlarından seçiliyor. Test kaydı hiçbir aşamada görülmüyor.
    Dönen tablo, her test uçuşunun skoru ve o katın eşiği ile birlikte.
    """
    gruplar = sorted({kayit_adi(u) for u, _ in veri})
    sonuclar, skorlar = [], {}
    for g in gruplar:
        egitim = [(u, d) for u, d in veri if kayit_adi(u) != g]
        test = [(u, d) for u, d in veri if kayit_adi(u) == g]
        y = yontem_sinifi(**ayar).egit(egitim)
        esik = esik_sec([egitim_ozeti(y, u, d) for u, d in egitim])
        for u, d in test:
            s = y.skor(d)
            skorlar[u.ad] = (d["t"].to_numpy(), s, esik)
            t = d["t"].to_numpy()
            nominal_s = float(np.sum((t >= ISINMA_S) & (t < (u.ariza_baslangic or np.inf))) * DT)
            sonuclar.append(Sonuc(u.ad, u.tip, u.ariza_baslangic, ilk_alarm(t, s, esik), nominal_s))
    return sonuclar, skorlar


def sonuc_tablosu(sonuclar):
    return pd.DataFrame([
        {"uçuş": s.ucus, "tip": s.tip, "arıza_s": s.ariza_s, "alarm_s": s.alarm_s,
         "durum": s.durum, "gecikme_s": s.gecikme}
        for s in sonuclar
    ])
