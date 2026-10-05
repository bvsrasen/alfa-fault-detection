from pathlib import Path

import numpy as np
import pandas as pd

from alfa.veri import liste_oku
from alfa.yontemler import Lojistik, kalici_min

HIZALI = Path(__file__).parent.parent / "veri" / "hizali"


def test_kalici_min():
    x = np.array([0, 5, 5, 5, 1, 5])
    s = kalici_min(x, 3)
    assert np.isneginf(s[:2]).all()
    assert list(s[2:]) == [0, 5, 1, 1]


def test_c_kanallari_python_ile_ayni():
    # C kodu kanal yapısını sabit kodluyor; Python'da değişirse C de değişmeli
    from alfa.c_arayuz import C_KANALLARI
    from alfa.yontemler import KANALLAR

    assert KANALLAR == C_KANALLARI


def test_lojistik_arizadan_sonra_daha_yuksek():
    # İki gerçek uçuşla eğitilen model, rudder arızasından sonraki logit'i
    # arızadan öncekinden belirgin şekilde yüksek bulmalı
    adlar = ("carbonZ_2018-09-11-15-06-34_1_rudder_right_failure", "carbonZ_2018-10-05-14-34-20_1_no_failure")
    ucuslar = {u.ad: u for u in liste_oku(HIZALI / "ucuslar.csv")}
    egitim = [(ucuslar[a], pd.read_csv(HIZALI / f"{a}.csv")) for a in adlar]
    model = Lojistik().egit(egitim)

    u, d = egitim[0]
    X = model.ozellikler(d)
    assert X.shape == (len(d), 25)
    logit = model.logit(d)
    t = d["t"].to_numpy()
    once = logit[(t >= 15) & (t < u.ariza_baslangic)]
    sonra = logit[t >= u.ariza_baslangic + 2]
    assert np.median(sonra) > np.median(once) + 2
