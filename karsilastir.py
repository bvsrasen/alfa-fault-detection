"""İki yöntemi kayıt bazlı çapraz doğrulamayla karşılaştırır.

    python karsilastir.py   # docs/sonuclar.md ve docs/ornek_tespit.png

Her yöntem 30 katta, bir kaydı dışarıda bırakarak eğitiliyor; eşik de o
katın eğitim uçuşlarından seçiliyor. Tablodaki her sayı, modelin eğitimde
hiç görmediği uçuşlardan geliyor.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from alfa import degerlendirme as de
from alfa.degerlendirme import capraz_dogrula, metrikler, sonuc_tablosu
from alfa.veri import yukle
from alfa.yontemler import Esik, Lojistik

YONTEMLER = [
    ("Takip hatası eşiği", Esik),
    ("Lojistik regresyon", Lojistik),
]
SECILEN = "Lojistik regresyon"

RENKLER = ["#2a78d6", "#eb6834"]
MUREKKEP, IKINCIL, ZEMIN = "#0b0b0b", "#52514e", "#fcfcfb"


def md_tablo(df, ondalik=2):
    def bicim(x):
        if x is None or (isinstance(x, float) and np.isnan(x)):
            return "-"
        if isinstance(x, (float, np.floating)):
            return f"{x:.{ondalik}f}"
        return str(x)

    satirlar = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    # iterrows satırı tek tipe çeviriyor (tamsayılar 46.00 oluyor), itertuples çevirmiyor
    for r in df.itertuples(index=False):
        satirlar.append("| " + " | ".join(bicim(x) for x in r) + " |")
    return "\n".join(satirlar)


def eksen_sade(ax):
    ax.set_facecolor(ZEMIN)
    for k in ("top", "right"):
        ax.spines[k].set_visible(False)
    ax.tick_params(colors=IKINCIL, labelsize=8)
    ax.grid(alpha=0.25, lw=0.5)


def ornek_ucuslar(tablo):
    """Grafikte gösterilecek dört uçuş: yakalanan bir motor ve bir rudder
    arızası, bir aileron uçuşu (varsa kaçırılan) ve bir arızasız uçuş (varsa
    yanlış alarm veren). Başarılı ve başarısız örnekler birlikte görünsün."""
    def ilk(tip, durumlar):
        for durum in durumlar:
            satir = tablo[(tablo["tip"] == tip) & (tablo["durum"] == durum)]
            if len(satir):
                return satir["uçuş"].iloc[0]
        return tablo.loc[tablo["tip"] == tip, "uçuş"].iloc[0]

    return [ilk("engines", ["DP"]), ilk("rudder", ["DP"]),
            ilk("aileron", ["YN", "YP", "DP"]), ilk("arızasız", ["YP", "DN"])]


def ornek_ciz(skor, veri, adlar, yol):
    bilgi = {u.ad: u for u, _ in veri}
    fig, axs = plt.subplots(len(adlar), 1, figsize=(8, 2.4 * len(adlar)))
    fig.patch.set_facecolor(ZEMIN)
    for ax, ad in zip(axs, adlar):
        eksen_sade(ax)
        t, s, esik = skor[ad]
        u = bilgi[ad]
        m = (t >= de.ISINMA_S) & np.isfinite(s)
        ax.plot(t[m], s[m], color=RENKLER[0], lw=1.5)
        ax.axhline(esik, color=IKINCIL, lw=1, ls=":")
        if u.ariza_var:
            ax.axvline(u.ariza_baslangic, color=MUREKKEP, lw=1, ls="--")
            ax.text(u.ariza_baslangic, 1.0, "arıza ", transform=ax.get_xaxis_transform(),
                    color=MUREKKEP, fontsize=8, va="top", ha="right")
        alarm = t[(s > esik) & (t >= de.ISINMA_S)]
        if len(alarm):
            ax.axvline(alarm[0], color=RENKLER[1], lw=1.5)
            ax.text(alarm[0], 1.0, " alarm", transform=ax.get_xaxis_transform(), color=RENKLER[1], fontsize=8, va="top")
        ax.set_title(ad.removeprefix("carbonZ_"), fontsize=9, color=MUREKKEP, loc="left")
        ax.set_ylabel("skor (logit)", color=IKINCIL, fontsize=8)
    axs[-1].set_xlabel("Zaman (s)", color=IKINCIL)
    fig.tight_layout()
    fig.savefig(yol, dpi=130)
    plt.close(fig)


def main():
    veri = yukle()
    sonuclar = {}
    for ad, sinif in YONTEMLER:
        sonuclar[ad] = capraz_dogrula(sinif, veri)
        print(f"{ad}: bitti")
    ozet = pd.DataFrame([{"yöntem": ad, **metrikler(son)} for ad, (son, _) in sonuclar.items()])
    nominal_saat = sum(x.nominal_s for x in sonuclar[SECILEN][0]) / 3600

    # Tip ve emr kırılımı: her hücre "yakalanan/toplam (medyan gecikme s)"
    kirilim = []
    for ad, (son, _) in sonuclar.items():
        df = sonuc_tablosu(son)
        df["grup"] = df["tip"] + np.where(df["uçuş"].str.contains("emr_traj"), " (emr)", "")
        satir = {"yöntem": ad}
        for g, alt in df.groupby("grup"):
            if g.startswith("arızasız"):
                satir[g] = f"{(alt['durum'] == 'YP').sum()}/{len(alt)} YP"
                continue
            dp = alt[alt["durum"] == "DP"]
            gec = f" ({dp['gecikme_s'].median():.1f} s)" if len(dp) else ""
            yp = (alt["durum"] == "YP").sum()
            satir[g] = f"{len(dp)}/{len(alt)}{gec}" + (f", {yp} YP" if yp else "")
        kirilim.append(satir)
    kirilim = pd.DataFrame(kirilim)

    secilen = sonuc_tablosu(sonuclar[SECILEN][0])

    # Isınma süresinin etkisi: aynı yöntem, farklı ısınma süreleriyle
    hassasiyet = []
    varsayilan = de.ISINMA_S
    for isinma in (5.0, 10.0, 15.0, 20.0):
        if isinma == varsayilan:
            son = sonuclar[SECILEN][0]  # yukarıda zaten hesaplandı
        else:
            de.ISINMA_S = isinma
            son, _ = capraz_dogrula(Lojistik, veri)
        hassasiyet.append({"ısınma_s": isinma, **metrikler(son)})
    de.ISINMA_S = varsayilan
    hassasiyet = pd.DataFrame(hassasiyet)

    Path("docs").mkdir(exist_ok=True)
    ornek_ciz(sonuclar[SECILEN][1], veri, ornek_ucuslar(secilen), "docs/ornek_tespit.png")

    metin = f"""# Sonuçlar

`python karsilastir.py` ile üretildi. Etiketli 46 uçuş, 30 kayıt. Her yöntem
bir kaydı dışarıda bırakarak 30 kez eğitildi, eşik her katta yalnızca eğitim
uçuşlarından seçildi (eğitim doğruluğunu en büyük yapan eşik). Tablodaki
her uçuşun sonucu, o uçuşu hiç görmemiş bir modelden.

Metrikler ALFA makalesindeki tanımlarla, uçuş bazında: arızadan önce
verilen tek alarm o uçuşu YP yapar; tespit süreleri yalnızca DP uçuşlardan.

## Özet

{md_tablo(ozet)}

`YP_saat`: yanlış alarm veren uçuş sayısı bölü toplam nominal uçuş süresi
(ısınmadan sonra, arızadan önce; toplam {nominal_saat:.2f} saat).

## Arıza tipine göre

Hücreler: yakalanan / toplam (medyan tespit süresi), varsa arızadan önce
alarm veren (YP) uçuş sayısı. "(emr)" uçuşlarında arızadan ~0,07 s sonra
gemideki acil durum yörüngesi devreye giriyor; komut tarafındaki sinyaller
o andan sonra gerçek etiketi bilen bir sistemden etkileniyor. O yüzden ayrı.

{md_tablo(kirilim)}

## Isınma süresinin etkisi ({SECILEN})

Kayıtların başında otonom moda geçişin geçici rejimi var (hız 23 m/s'den
13 m/s'ye iniyor, 45° roll komutları). Bu süre boyunca alarm verilmiyor ve
bu örnekler eğitime girmiyor. Varsayılan {varsayilan:g} s. Aşağıdaki tablo
farklı değerlerle ne olduğunu gösteriyor; aradaki fark, 46 uçuşla ne kadar
oynama beklenmesi gerektiğini de gösteriyor.

{md_tablo(hassasiyet)}

## {SECILEN}: uçuş uçuş

{md_tablo(secilen)}

![Örnek tespitler](ornek_tespit.png)
"""
    Path("docs/sonuclar.md").write_text(metin, encoding="utf-8")
    print(metin)


if __name__ == "__main__":
    main()
