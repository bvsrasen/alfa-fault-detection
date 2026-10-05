"""C dedektörünü gerçek uçuşlarla Python'a karşı doğrular.

    python c_dogrula.py   # c/alfa_param.c, docs/c_dogrulama.md, tests/ornek/c/

Bütün etiketli uçuşlarla eğitilen modeli c/alfa_param.c olarak yazar, C
kodunu derler, sonra 47 uçuşun hepsini hem Python'dan hem C'den geçirip
logit, skor ve alarm anını karşılaştırır.
"""
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from alfa import c_arayuz as ca
from alfa import degerlendirme as de
from alfa.veri import yukle
from alfa.yontemler import Lojistik
from alfa.zaman import DT

# Testlerde kullanılan kısa ve alarm veren bir uçuş
TEST_UCUSU = "carbonZ_2018-09-11-15-06-34_1_rudder_right_failure"


def ilk_alarm_c(c):
    i = np.flatnonzero(c["alarm"].to_numpy() == 1)
    return float(c["t"].iloc[i[0]]) if len(i) else None


def main():
    veri = yukle()
    tum = yukle(etiketsizi_al=True)

    model = Lojistik().egit(veri)
    esik = de.esik_sec([de.egitim_ozeti(model, u, d) for u, d in veri])
    ca.kaynak_yaz(ca.parametreler(model, esik), ca.C_KLASOR / "alfa_param.c",
                  f"{len(veri)} etiketli ALFA uçuşuyla eğitildi")
    ca.derle()

    satirlar = []
    for u, d in tum:
        c = ca.calistir(d)
        py_logit = model.logit(d)
        py_skor = model.skor(d)
        sonlu = np.isfinite(py_skor)
        py_alarm = de.ilk_alarm(d["t"].to_numpy(), py_skor, esik)
        c_alarm = ilk_alarm_c(c)
        ayni = (py_alarm is None and c_alarm is None) or (
            py_alarm is not None and c_alarm is not None and abs(py_alarm - c_alarm) < DT / 2)
        satirlar.append({
            "uçuş": u.ad.removeprefix("carbonZ_"),
            "örnek": len(d),
            "maks_logit_farkı": f"{np.abs(c['logit'].to_numpy() - py_logit).max():.1e}",
            "maks_skor_farkı": f"{np.abs(c['skor'].to_numpy()[sonlu] - py_skor[sonlu]).max():.1e}",
            "alarm_py": "-" if py_alarm is None else f"{py_alarm:.1f}",
            "alarm_c": "-" if c_alarm is None else f"{c_alarm:.1f}",
            "alarm_aynı": ayni,
        })
    tablo = pd.DataFrame(satirlar)

    bilgi = subprocess.run([str(ca.CLI), "--bilgi"], capture_output=True, text=True, check=True).stdout
    try:
        arm = subprocess.run(["make", "-s", "-C", str(ca.C_KLASOR), "arm"],
                             capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        arm = "arm-none-eabi-gcc bulunamadı"

    satir = ["| " + " | ".join(tablo.columns) + " |", "|" + "---|" * len(tablo.columns)]
    satir += ["| " + " | ".join(map(str, r)) + " |" for r in tablo.itertuples(index=False)]

    metin = f"""# C dedektörünün doğrulanması

`python c_dogrula.py` ile üretildi.

Model {len(veri)} etiketli uçuşun hepsiyle eğitildi (eşik {esik:.4f}) ve
`c/alfa_param.c` olarak yazıldı. Sonra {len(tum)} uçuşun hepsi (etiketsiz olan
dahil) hem Python'dan hem derlenmiş C kodundan geçirildi.

- Alarm anı aynı olan uçuş: {tablo['alarm_aynı'].sum()} / {len(tablo)}

C 32 bitlik, Python 64 bitlik kayan nokta sayılarla hesaplıyor; aradaki
küçük farklar bu yüzden. Bu tablo bir başarı ölçüsü değil (model bu
uçuşlarla eğitildi), sadece iki kodun aynı şeyi hesapladığının kontrolü.

{chr(10).join(satir)}

## Bellek ve kod boyutu

```
{bilgi.strip()}
```

Cortex-M4F için (`make -C c arm`, `-Os`):

```
{arm.strip()}
```

`alfa_tespit_m4.o` kod, `alfa_param_m4.o` katsayılar (ikisi de Flash'ta).
RAM'de tek gereken `alfa_durum_t`.
"""
    Path("docs/c_dogrulama.md").write_text(metin, encoding="utf-8")
    print(metin)

    # Testler için gerçek bir uçuştan girdi ve Python'un beklenen çıktısı
    d = next(tablo for u, tablo in veri if u.ad == TEST_UCUSU)
    klasor = Path("tests/ornek/c")
    klasor.mkdir(parents=True, exist_ok=True)
    d[ca.GIRDI_SUTUNLARI].to_csv(klasor / "girdi.csv", index=False, float_format="%.9g")
    pd.DataFrame({"t": d["t"], "logit": model.logit(d), "skor": model.skor(d)}).to_csv(
        klasor / "beklenen.csv", index=False, float_format="%.9g")


if __name__ == "__main__":
    main()
