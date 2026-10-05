"""Etiket sızıntısının etkisi: arızanın uygulandığı çıkışa bakan tek kural.

    python sizinti.py   # docs/sizinti.md (ham veri gerekir: python veri_indir.py)

ALFA'da arıza, servo/motor çıkışı sabit bir PWM'e kilitlenerek uygulanmış.
"Herhangi bir rc-out kanalı T saniyedir hiç değişmiyorsa alarm" kuralı
eğitim gerektirmiyor ve hiçbir fizik bilgisi kullanmıyor. Bu kuralın aldığı
sonuç, bu sinyalleri girdi olarak alan bir yöntemin ne kadar iyi
görünebileceğini gösteriyor.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from alfa.degerlendirme import ISINMA_S, Sonuc, metrikler, sonuc_tablosu
from alfa.okuma import ucuslari_ac

KANALLAR = [f"channels{i}" for i in range(1, 6)]  # elevator, gaz, rudder, aileronlar
SURELER_S = (2.0, 3.0, 4.0, 6.0)


def kilit_alarmi(rc, sure_s):
    """Bir kanalın değeri sure_s boyunca değişmediği ilk an."""
    t = rc["t"].to_numpy()
    X = rc[KANALLAR].to_numpy()
    degisim = np.empty_like(X, dtype=float)
    degisim[0] = t[0]
    for k in range(1, len(t)):
        degisim[k] = np.where(X[k] == X[k - 1], degisim[k - 1], t[k])
    kilitli = ((t[:, None] - degisim) >= sure_s).any(axis=1) & (t >= ISINMA_S)
    i = np.flatnonzero(kilitli)
    return float(t[i[0]]) if len(i) else None


def md_tablo(df):
    def bicim(x):
        if x is None or (isinstance(x, float) and np.isnan(x)):
            return "-"
        return f"{x:.2f}" if isinstance(x, float) else str(x)

    satirlar = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    satirlar += ["| " + " | ".join(bicim(x) for x in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(satirlar)


def main():
    ucuslar = [u for u in ucuslari_ac() if not u.etiket_yok]
    rc = {u.ad: u.oku("mavros-rc-out") for u in ucuslar}
    # saat başına yanlış alarm için: ısınmadan sonra, arızadan önce geçen süre
    nominal = {}
    for u in ucuslar:
        son_t = rc[u.ad]["t"].iloc[-1]
        nominal[u.ad] = max(0.0, min(u.ariza_baslangic or son_t, son_t) - ISINMA_S)

    ozet, kirilim = [], []
    for sure in SURELER_S:
        son = [Sonuc(u.ad, u.tip, u.ariza_baslangic, kilit_alarmi(rc[u.ad], sure), nominal[u.ad])
               for u in ucuslar]
        ozet.append({"kilit_s": sure, **metrikler(son)})
        df = sonuc_tablosu(son)
        satir = {"kilit_s": sure}
        for tip, alt in df.groupby("tip"):
            satir[tip] = f"{(alt['durum'] == 'DP').sum()}/{len(alt)}" if alt["arıza_s"].notna().any() \
                else f"{(alt['durum'] == 'YP').sum()}/{len(alt)} YP"
        kirilim.append(satir)

    metin = f"""# Etiket sızıntısının etkisi

`python sizinti.py` ile üretildi. Kural: `rc-out`'taki beş kontrol kanalından
biri `kilit_s` saniyedir hiç değişmiyorsa alarm. Eğitim yok, fizik yok;
yalnızca arızanın uygulandığı çıkışa bakıyor. Metrikler ve ısınma süresi
[sonuclar.md](sonuclar.md) ile aynı.

{md_tablo(pd.DataFrame(ozet))}

Arıza tipine göre yakalanan (arızasız uçuşlarda yanlış alarm):

{md_tablo(pd.DataFrame(kirilim))}

Kanal 6 saniye kilitli kalınca alarm veren bu kural, sızıntısız yöntemlerin
hiçbirinin yaklaşamadığı bir sonuç alıyor ve aileron arızalarını da
kaçırmıyor. Oysa fiziksel sinyallerde aileron arızası çok zayıf bir iz
bırakıyor (bkz. [sonuclar.md](sonuclar.md)). Bu sinyaller (ya da onlardan
türeyen gaz değeri) bir yöntemin girdisinde varsa, sonucun ne kadarının
sızıntıdan geldiğini ayırmak mümkün değil. Bu projedeki yöntemlerin hiçbiri bunları
kullanmıyor.
"""
    Path("docs/sizinti.md").write_text(metin, encoding="utf-8")
    print(metin)


if __name__ == "__main__":
    main()
