"""ALFA veri setinin işlenmiş hâlini (processed.zip) KiltHub'dan indirip açar.

Veri seti: Keipour, Mousaei, Scherer, "ALFA: A Dataset for UAV Fault and
Anomaly Detection", KiltHub, doi:10.1184/R1/12707963.v1

    python veri_indir.py            # veri/processed/ altına açar
    python veri_indir.py --hedef X  # başka bir klasöre
"""
import argparse
import hashlib
import urllib.request
import zipfile
from pathlib import Path

# KiltHub, Figshare altyapısında çalışıyor; dosyanın kendisi ndownloader'dan iniyor
URL = "https://ndownloader.figshare.com/files/24095870"
MD5 = "792c36aef2fd1fd19a91a53e3b3dcfdf"  # KiltHub'daki dosya kaydından
UCUS_SAYISI = 47


def md5(yol):
    h = hashlib.md5()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


def indir(url, yol):
    gecici = yol.with_suffix(".part")
    with urllib.request.urlopen(url, timeout=60) as yanit, open(gecici, "wb") as f:
        toplam = int(yanit.headers.get("Content-Length", 0))
        inen = 0
        while parca := yanit.read(1 << 20):
            f.write(parca)
            inen += len(parca)
            if toplam:
                print(f"\r  {inen / 1e6:6.0f} / {toplam / 1e6:.0f} MB", end="", flush=True)
    print()
    gecici.rename(yol)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hedef", default="veri", help="indirme klasörü (varsayılan: veri)")
    args = ap.parse_args()

    hedef = Path(args.hedef)
    hedef.mkdir(parents=True, exist_ok=True)
    zip_yolu = hedef / "processed.zip"

    if zip_yolu.exists() and md5(zip_yolu) == MD5:
        print(f"{zip_yolu} zaten var, indirme atlandı")
    else:
        print(f"indiriliyor: {URL}")
        indir(URL, zip_yolu)
        if md5(zip_yolu) != MD5:
            raise SystemExit(f"{zip_yolu}: MD5 tutmuyor, dosya bozuk inmiş olabilir")

    # Zip'te bag ve mat dosyaları da var; sadece CSV'ler lazım
    with zipfile.ZipFile(zip_yolu) as z:
        csvler = [a for a in z.namelist() if a.endswith(".csv")]
        z.extractall(hedef, members=csvler)

    ucuslar = [p for p in (hedef / "processed").iterdir() if p.is_dir()]
    print(f"{len(csvler)} CSV, {len(ucuslar)} uçuş -> {hedef / 'processed'}")
    if len(ucuslar) != UCUS_SAYISI:
        print(f"uyarı: {UCUS_SAYISI} uçuş bekleniyordu")


if __name__ == "__main__":
    main()
