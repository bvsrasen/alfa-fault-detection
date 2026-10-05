"""Repodaki 10 Hz tablolar (veri/hizali) tutarlı mı."""
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

from alfa.veri import kayit_adi, yukle
from alfa.zaman import DT

HIZALI = Path(__file__).parent.parent / "veri" / "hizali"


@pytest.fixture(scope="module")
def veri():
    # ham veri olmasa bile repodaki tablolarla çalışmalı
    return yukle(kok=HIZALI / "olmayan_klasor", onbellek=HIZALI, etiketsizi_al=True)


def test_ucus_dagilimi(veri):
    tipler = Counter(u.tip for u, _ in veri)
    assert len(veri) == 47
    assert tipler["engines"] == 23
    assert tipler["arızasız"] == 10
    assert tipler["etiketsiz"] == 1
    assert len({kayit_adi(u) for u, _ in veri if not u.etiket_yok}) == 30


def test_tablolar(veri):
    for u, d in veri:
        t = d["t"].to_numpy()
        assert np.allclose(np.diff(t), DT), u.ad
        assert not d.isna().any().any(), u.ad
        if u.ariza_var:
            assert (d["ariza"] == (t >= u.ariza_baslangic)).all(), u.ad
        else:
            assert not d["ariza"].any(), u.ad


def test_bilinen_ariza_ani(veri):
    u = next(u for u, _ in veri if u.ad == "carbonZ_2018-07-18-15-53-31_1_engine_failure")
    assert u.ariza_baslangic == pytest.approx(116.259452995, abs=1e-9)
