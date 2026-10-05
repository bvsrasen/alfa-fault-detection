# Veri

Bu klasördeki tablolar ALFA veri setinin işlenmiş kayıtlarından
(`processed.zip`) üretildi. Her uçuş için bir CSV dosyası var ve bütün
sinyaller saniyede 10 örneklik ortak bir zaman çizelgesine getirildi. Her
satırda, her sinyalin o ana kadar gelen son değeri bulunuyor. Bu işlem
`alfa/zaman.py` dosyasında yapılıyor. Projedeki bütün analizler bu
tablolarla çalıştığı için ham veriyi indirmek gerekmiyor.

| sütun | birim | anlamı | kaynak kayıt |
|---|---|---|---|
| `t` | s | kaydın başından geçen süre | |
| `p`, `q`, `r` | rad/s | gövde ekseninde roll, pitch ve yaw hızları | `mavros/imu/data_raw` |
| `ax`, `ay`, `az` | m/s^2 | ivmeölçerin ölçtüğü ileri, yanal ve dikey ivme | `mavros/imu/data_raw` |
| `roll_k`, `pitch_k` | derece | otopilotun istediği yatış ve pitch açısı | `mavros/nav_info/roll`, `pitch` |
| `roll`, `pitch`, `yaw` | derece | ölçülen yönelim | `mavros/nav_info/roll`, `pitch`, `yaw` |
| `vn`, `ve`, `vd` | m/s | kuzey, doğu ve aşağı yöndeki hız | `mavros/nav_info/velocity` |
| `basinc` | Pa | barometrik basınç | `mavros/imu/atm_pressure` |
| `alt_hata` | m | otopilotun irtifa hatası | `mavros/nav_info/errors` |
| `hiz_hata` | cm/s | otopilotun hava hızı hatası | `mavros/nav_info/errors` |
| `ariza` | | o anda arızanın başlamış olup olmadığı | |

`ariza` sütunu yalnızca sonuçları değerlendirmek için kullanılıyor, modele
girdi olarak verilmiyor.

`hizali/ucuslar.csv` dosyasında uçuşların adları ve arızalı uçuşlarda
arızanın kaydın başından kaç saniye sonra başladığı yazıyor. Bu zamanı
orijinal kayıtlardaki `failure_status` mesajının ilk geldiği andan aldım.
Arızasız uçuşlarda bu alan boş.

Arızanın uygulandığı çıkış sinyallerini (`rc-out`) ve gaz değerini bu
tablolara bilerek almadım. Bu sinyaller arızanın kendisini doğrudan
gösterdiği için, kullanılsalardı yapılan tespit gerçek olmazdı (ayrıntısı
[docs/sizinti.md](../docs/sizinti.md) dosyasında).

Tabloları ham veriden baştan üretmek isterseniz:

```
python veri_indir.py      # ham veriyi indirir
rm -r veri/hizali         # mevcut tabloları siler
python karsilastir.py     # tablolar ham veriden yeniden üretilir
```

Kaynak: A. Keipour, M. Mousaei, S. Scherer, "ALFA: AIR Lab Failure and
Anomaly Dataset", Carnegie Mellon University, KiltHub, 2020,
[doi:10.1184/R1/12707963.v1](https://doi.org/10.1184/R1/12707963.v1).
Veri setinin lisansı CC BY 4.0.
