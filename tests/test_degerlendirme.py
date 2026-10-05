import numpy as np

from alfa.degerlendirme import ISINMA_S, Sonuc, esik_sec, ilk_alarm, metrikler


def test_durumlar():
    assert Sonuc("a", "engines", 100.0, 102.5).durum == "DP"
    assert Sonuc("a", "engines", 100.0, 102.5).gecikme == 2.5
    assert Sonuc("a", "engines", 100.0, 99.0).durum == "YP"
    assert Sonuc("a", "engines", 100.0, None).durum == "YN"
    assert Sonuc("a", "arızasız", None, None).durum == "DN"
    assert Sonuc("a", "arızasız", None, 50.0).durum == "YP"


def test_metrikler_makaledeki_tanimlarla():
    sonuclar = [
        Sonuc("1", "engines", 100.0, 101.0),  # DP, 1 s
        Sonuc("2", "engines", 100.0, 103.0),  # DP, 3 s
        Sonuc("3", "engines", 100.0, 50.0),   # YP
        Sonuc("4", "rudder", 60.0, None),     # YN
        Sonuc("5", "arızasız", None, None),   # DN
    ]
    m = metrikler(sonuclar)
    assert (m["DP"], m["YP"], m["YN"], m["DN"]) == (2, 1, 1, 1)
    assert m["doğruluk"] == 3 / 5
    assert m["kesinlik"] == 2 / 3
    assert m["duyarlılık"] == 2 / 4  # arızalı 4 uçuş
    assert m["ort_tespit_s"] == 2.0
    assert m["maks_tespit_s"] == 3.0


def test_isinmada_alarm_yok():
    t = np.arange(0, ISINMA_S + 10, 0.1)
    skor = np.full_like(t, 5.0)
    assert ilk_alarm(t, skor, 1.0) >= ISINMA_S


def test_esik_sec_aralik_ortasi():
    # (nominal maks, arızadan sonra maks, arızalı mı)
    egitim = [(1.0, 5.0, True), (2.0, 6.0, True), (1.5, -np.inf, False)]
    # 2 ile 5 arasındaki her eşik üç uçuşu da doğru sınıflıyor
    h = esik_sec(egitim)
    assert h == 3.5


def test_esik_sec_bos():
    import pytest

    with pytest.raises(ValueError):
        esik_sec([(-np.inf, -np.inf, False)])
