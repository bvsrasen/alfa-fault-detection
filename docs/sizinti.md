# Etiket sızıntısının etkisi

`python sizinti.py` ile üretildi. Kural: `rc-out`'taki beş kontrol kanalından
biri `kilit_s` saniyedir hiç değişmiyorsa alarm. Eğitim yok, fizik yok;
yalnızca arızanın uygulandığı çıkışa bakıyor. Metrikler ve ısınma süresi
[sonuclar.md](sonuclar.md) ile aynı.

| kilit_s | uçuş | DP | YP | YN | DN | doğruluk | kesinlik | duyarlılık | ort_tespit_s | maks_tespit_s | YP_saat |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2.00 | 46 | 25 | 16 | 0 | 5 | 0.65 | 0.61 | 0.69 | 2.48 | 3.13 | 17.76 |
| 3.00 | 46 | 34 | 5 | 0 | 7 | 0.89 | 0.87 | 0.94 | 3.53 | 4.09 | 5.55 |
| 4.00 | 46 | 35 | 2 | 0 | 9 | 0.96 | 0.95 | 0.97 | 4.48 | 4.96 | 2.22 |
| 6.00 | 46 | 36 | 1 | 0 | 9 | 0.98 | 0.97 | 1.00 | 6.47 | 6.93 | 1.11 |

Arıza tipine göre yakalanan (arızasız uçuşlarda yanlış alarm):

| kilit_s | aileron | aileron+rudder | arızasız | elevator | engines | rudder |
|---|---|---|---|---|---|---|
| 2.00 | 6/7 | 0/1 | 5/10 YP | 1/2 | 16/23 | 2/3 |
| 3.00 | 6/7 | 1/1 | 3/10 YP | 2/2 | 22/23 | 3/3 |
| 4.00 | 6/7 | 1/1 | 1/10 YP | 2/2 | 23/23 | 3/3 |
| 6.00 | 7/7 | 1/1 | 1/10 YP | 2/2 | 23/23 | 3/3 |

Kanal 6 saniye kilitli kalınca alarm veren bu kural, sızıntısız yöntemlerin
hiçbirinin yaklaşamadığı bir sonuç alıyor ve aileron arızalarını da
kaçırmıyor. Oysa fiziksel sinyallerde aileron arızası çok zayıf bir iz
bırakıyor (bkz. [sonuclar.md](sonuclar.md)). Bu sinyaller (ya da onlardan
türeyen gaz değeri) bir yöntemin girdisinde varsa, sonucun ne kadarının
sızıntıdan geldiğini ayırmak mümkün değil. Bu projedeki yöntemlerin hiçbiri bunları
kullanmıyor.
