from pathlib import Path

import pytest

from alfa.okuma import ucus_ac, ucuslari_ac

# tests/ornek: iki gerçek ALFA uçuşunun ilk birkaç satırı
ORNEK = Path(__file__).parent / "ornek"
VERI = Path(__file__).parent.parent / "veri" / "processed"


def test_ariza_baslangici_ilk_mesajdan():
    u = ucus_ac(ORNEK / "carbonZ_2018-07-18-15-53-31_1_engine_failure")
    # failure_status-engines ilk mesajı 1531943927129305993 ns, roll ilk mesajı 1531943810869852998 ns
    assert u.ariza_baslangic == pytest.approx(116.259452995, abs=1e-6)
    assert u.tip == "engines"


def test_arizasiz_ucus():
    u = ucus_ac(ORNEK / "carbonZ_2018-07-18-16-37-39_1_no_failure")
    assert not u.ariza_var
    assert u.ariza_baslangic is None
    assert u.tip == "arızasız"


def test_oku_zaman_ve_sutunlar():
    u = ucus_ac(ORNEK / "carbonZ_2018-07-18-15-53-31_1_engine_failure")
    df = u.oku("mavros-nav_info-roll")
    assert df["t"].iloc[0] == 0.0
    assert df["t"].is_monotonic_increasing
    assert {"commanded", "measured", "header.stamp"} <= set(df.columns)


def test_olmayan_klasor():
    with pytest.raises(FileNotFoundError):
        ucuslari_ac(ORNEK / "yok")


@pytest.mark.skipif(not VERI.is_dir(), reason="ALFA verisi indirilmemiş")
def test_tam_veri_dagilimi():
    # veri setinin yayımlanan dağılımı: 23 motor, 10 arızasız, 1 etiketsiz
    tipler = [u.tip for u in ucuslari_ac(VERI)]
    assert len(tipler) == 47
    assert tipler.count("engines") == 23
    assert tipler.count("arızasız") == 10
    assert tipler.count("etiketsiz") == 1
