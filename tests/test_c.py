"""C dedektörü, aynı uçuş için Python'un ürettiği logit ve skorla karşılaştırılıyor.

tests/ornek/c altındaki dosyaları `python c_dogrula.py` gerçek bir ALFA
uçuşundan üretiyor (2018-09-11-15-06-34_1_rudder_right_failure).
"""
import shutil
import subprocess
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

KOK = Path(__file__).parent.parent
ORNEK = Path(__file__).parent / "ornek" / "c"
CLI = KOK / "c" / "build" / "alfa_cli"

pytestmark = pytest.mark.skipif(shutil.which("make") is None or shutil.which("gcc") is None,
                                reason="C derleyicisi yok")


@pytest.fixture(scope="module", autouse=True)
def derle():
    subprocess.run(["make", "-s", "-C", str(KOK / "c")], check=True)


def calistir(girdi):
    cikti = subprocess.run([str(CLI)], input=girdi, capture_output=True, text=True, check=True).stdout
    return pd.read_csv(StringIO(cikti))


def test_python_ile_ayni():
    c = calistir((ORNEK / "girdi.csv").read_text())
    beklenen = pd.read_csv(ORNEK / "beklenen.csv")
    assert len(c) == len(beklenen)
    # C 32 bit, Python 64 bit hesaplıyor; fark küçük kalmalı
    assert np.allclose(c["logit"], beklenen["logit"], atol=1e-4)
    sonlu = np.isfinite(beklenen["skor"])
    assert (np.isinf(c["skor"]) == ~sonlu).all()
    assert np.allclose(c["skor"][sonlu], beklenen["skor"][sonlu], atol=1e-4)


def test_alarm_kalici():
    a = calistir((ORNEK / "girdi.csv").read_text())["alarm"].to_numpy()
    assert a.any(), "bu uçuşta alarm bekleniyor (rudder arızası)"
    assert (a[np.argmax(a):] == 1).all()


def test_bozuk_ornek_atlaniyor():
    # 300. örneğin roll'u NaN; dedektör bu satır hiç yokmuş gibi davranmalı
    satirlar = (ORNEK / "girdi.csv").read_text().splitlines()
    alanlar = satirlar[301].split(",")
    alanlar[7] = "nan"
    bozuk = satirlar[:301] + [",".join(alanlar)] + satirlar[302:]
    eksik = satirlar[:301] + satirlar[302:]

    a = calistir("\n".join(bozuk) + "\n")
    b = calistir("\n".join(eksik) + "\n")
    assert np.isnan(a["logit"].iloc[300])
    assert np.array_equal(a.drop(index=300)["logit"].to_numpy(), b["logit"].to_numpy())
