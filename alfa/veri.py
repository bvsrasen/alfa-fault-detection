"""Hizalanmış uçuş tabloları (veri/hizali/).

Ham CSV'lerden 10 Hz tabloya çevirmek birkaç saniye sürüyor, sonuç bir kere
yazılıp tekrar kullanılıyor. Tablolar ve uçuş listesi (ucuslar.csv) repoda
da var; ham veri indirilmeden bütün analizler bu tablolarla çalışıyor.
"""
from pathlib import Path

import pandas as pd

from alfa.okuma import Ucus, ucuslari_ac
from alfa.zaman import hizala

LISTE = "ucuslar.csv"


def liste_yaz(ucuslar, yol):
    satirlar = []
    for u in ucuslar:
        satirlar.append({
            "ad": u.ad,
            "arizalar": ";".join(f"{y}={t:.9f}" for y, t in u.arizalar.items()),
        })
    pd.DataFrame(satirlar).to_csv(yol, index=False)


def liste_oku(yol):
    ucuslar = []
    for r in pd.read_csv(yol, keep_default_na=False).itertuples():
        arizalar = {}
        for parca in filter(None, r.arizalar.split(";")):
            yuzey, t = parca.split("=")
            arizalar[yuzey] = float(t)
        ucuslar.append(Ucus(ad=r.ad, klasor=None, t0_ns=None, arizalar=arizalar))
    return ucuslar


def yukle(kok="veri/processed", onbellek="veri/hizali", etiketsizi_al=False):
    """[(Ucus, DataFrame), ...] döndürür. Etiketsiz uçuş varsayılan olarak dışarıda.

    Ham veri varsa eksik tablolar ondan üretiliyor; yoksa repodaki tablolar
    ve uçuş listesi kullanılıyor.
    """
    onbellek = Path(onbellek)
    if Path(kok).is_dir():
        onbellek.mkdir(parents=True, exist_ok=True)
        ucuslar = ucuslari_ac(kok)
        liste_yaz(ucuslar, onbellek / LISTE)
    elif (onbellek / LISTE).exists():
        ucuslar = liste_oku(onbellek / LISTE)
    else:
        raise FileNotFoundError(f"{kok} ve {onbellek / LISTE} yok; önce `python veri_indir.py` çalıştır")

    sonuc = []
    for u in ucuslar:
        if u.etiket_yok and not etiketsizi_al:
            continue
        yol = onbellek / f"{u.ad}.csv"
        if yol.exists():
            df = pd.read_csv(yol)
        else:
            df = hizala(u)
            df.to_csv(yol, index=False)
        sonuc.append((u, df))
    return sonuc


def kayit_adi(ucus):
    """Aynı kayıttan kesilmiş uçuşlar (..._1_, ..._2_) aynı grubu alıyor.

    Çapraz doğrulamada bunları ayırmazsak aynı gün, aynı rüzgâr ve aynı
    batarya ile uçmuş parçalar hem eğitimde hem testte olur.
    """
    return ucus.ad[len("carbonZ_"):len("carbonZ_") + 19]
