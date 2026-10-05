# İHA'da uçuş sırasında arıza tespiti

Bu projede sabit kanatlı bir insansız hava aracında motorun durması ya da bir
kontrol yüzeyinin takılı kalması gibi arızaları uçuş sırasında fark etmeye
çalıştım. Veri olarak Carnegie Mellon Üniversitesi'nin yayımladığı
[ALFA](http://theairlab.org/alfa-dataset) veri setini kullandım. Bu veri
setinde gerçek bir model uçakla yapılmış 47 uçuşun kaydı var.

Proje iki parçadan oluşuyor. İlk parçada Python ile bir tespit modeli
eğittim ve modeli eğitimde hiç görmediği uçuşlarda test ettim. İkinci parçada
aynı modeli STM32 gibi bir mikrodenetleyicide çalışabilecek şekilde C'ye
taşıdım ve C kodunun Python ile aynı sonucu verdiğini kontrol ettim.

Şu anki hâliyle model, test uçuşlarının %72'sini doğru sınıflandırıyor ve
arızayı ortalama 2,5 saniyede fark ediyor. Motor ve rudder arızalarını iyi
yakalıyor, aileron arızalarında ise zayıf kalıyor. Bunun nedenini aşağıda
anlattım.

![Dört uçuşta dedektörün skoru](docs/ornek_tespit.png)

Bu grafikte dört uçuş için modelin ürettiği skor görünüyor. Kesikli çizgi
arızanın başladığı anı, noktalı yatay çizgi alarm eşiğini, turuncu çizgi ise
alarmın verildiği anı gösteriyor. İlk iki uçuşta motor ve rudder arızası
birkaç saniye içinde yakalanıyor. Üçüncü uçuştaki aileron arızası hiç fark
edilmiyor. Dördüncü uçuşta arıza yok, ama model 59. saniye civarında yanlış
alarm veriyor.

## Veri

ALFA'daki 47 uçuşun 36'sında, uçuşun ortasında bilerek bir arıza
oluşturulmuş ve arızanın başladığı an kayıtlara yazılmış. Bunların 23'ünde
motor duruyor, 8'inde aileronlardan biri ya da ikisi takılıyor (birinde
rudder da takılıyor), 3'ünde rudder ve 2'sinde elevator takılıyor. 10 uçuşta
hiç arıza yok. Bir uçuşta ise arıza anı kaydedilmemiş, o yüzden onu
değerlendirmeye almadım.

Ham veri yaklaşık 330 MB olduğu için repoya koymadım; `veri_indir.py` onu
indiriyor. Onun yerine, işlenmiş hâlini `veri/hizali/` klasörüne koydum.
Böylece projeyi indiren biri ham veriye ihtiyaç duymadan bütün sonuçları
yeniden üretebiliyor. Tablolardaki sütunları
[veri/README.md](veri/README.md) dosyasında açıkladım.

## Nasıl çalışıyor

Kayıtlarda her sensör farklı bir hızda veri yazıyor. Bu yüzden önce bütün
sinyalleri saniyede 10 örneklik ortak bir zaman çizelgesine getirdim. Her an
için her sinyalin o ana kadar gelen son değerini kullandım. İki örnek
arasında ara değer hesaplamadım, çünkü bunun için bir sonraki örneği, yani
gelecekteki veriyi bilmek gerekir. Uçuş bilgisayarı da her an yalnızca son
gelen değeri bilir.

Modelin temel fikri şu: uçak normal uçarken bazı ölçümler diğerlerinden
tahmin edilebilir, arıza ise bu ilişkiyi bozar. Ben beş basit ilişki
kullandım:

| ölçüm | neye göre tahmin ediliyor |
|---|---|
| ileri ivme | otopilotun irtifa ve hız hatası, pitch açısı |
| yanal ivme | düzgün uçuşta sıfıra yakın olmalı |
| roll hızı | istenen ve ölçülen yatış açısı arasındaki fark |
| pitch hızı | istenen ve ölçülen pitch açısı arasındaki fark, yatış açısı |
| yaw hızı | yatış açısı ve hız (koordineli dönüş formülü) |

Her ilişki basit bir doğrusal denklem. Katsayılarını, eğitim uçuşlarının
arıza öncesi kısımlarından en küçük kareler yöntemiyle buldum. Uçuş
sırasında her ölçümün gerçek değeriyle tahmin edilen değeri arasındaki farka
"artık" diyorum. Normal uçuşta artıklar sıfır civarında dalgalanıyor. Motor
durduğunda ileri ivme beklenenin altına düşüyor, rudder takıldığında yanal
ivme bozuluyor.

Tek bir anlık değer gürültülü olabileceği için her artıktan beş değer
çıkardım: o anki değeri, mutlak değeri, son 1 ve 3 saniyedeki ortalaması ve
son 1 saniyedeki standart sapması. Böylece her an için 25 sayı elde ediliyor.
Bu 25 sayıyı lojistik regresyon modeline veriyorum. Model her sayıyı bir
ağırlıkla çarpıp topluyor ve sonuç ne kadar büyükse arıza ihtimalini o kadar
yüksek görüyor. Ağırlıkları, arızadan önceki ve sonraki örnekleri ayırt
edecek şekilde eğitim uçuşlarından öğreniyor.

Tek bir anlık sıçramanın alarm vermemesi için skorun yarım saniye boyunca
eşiğin üstünde kalmasını şart koştum. Eşiği, eğitim uçuşlarında doğru
sınıflanan uçuş sayısını en yüksek yapan değer olarak seçtim. Kodun büyük
kısmı `alfa/yontemler.py` ve `alfa/degerlendirme.py` dosyalarında.

## Nasıl test ettim

Bir modeli eğitildiği uçuşlarda test etmek, onu olduğundan iyi gösterir. Bu
yüzden her seferinde bazı uçuşları kenara ayırdım, modeli kalanlarla
eğittim ve kenara ayırdıklarımda test ettim. Burada dikkat ettiğim bir nokta
var: 46 uçuş aslında 30 ayrı kayıttan geliyor. Bazı uzun kayıtlar birkaç
uçuşa bölünmüş ve aynı kayıttan gelen uçuşlar aynı gün, aynı rüzgârda
yapıldığı için birbirine çok benziyor. Bu yüzden kenara her seferinde bir
kaydın bütün uçuşlarını birlikte ayırdım ve bunu 30 kaydın hepsi için
tekrarladım. Alarm eşiğini de her seferinde sadece eğitim uçuşlarından
seçtim.

Sonuçları ALFA makalesindeki gibi uçuş bazında değerlendirdim. Arızalı bir
uçuşta alarm arızadan sonra geldiyse doğru tespit sayılıyor. Arızadan önce
gelen tek bir alarm bile o uçuşu yanlış alarm yapıyor. Arızasız bir uçuşta
hiç alarm verilmemesi gerekiyor.

## Sonuçlar

Modeli, otopilotun istediği ve ölçülen yatış/pitch açıları arasındaki fark
belli bir sınırı geçince alarm veren basit bir yöntemle karşılaştırdım:

| yöntem | doğruluk | kesinlik | duyarlılık | ort. tespit süresi | en geç tespit | saatte yanlış alarm |
|---|---|---|---|---|---|---|
| takip hatası eşiği | 0.54 | 0.61 | 0.53 | 8.5 s | 21.2 s | 13.3 |
| lojistik regresyon | 0.72 | 0.80 | 0.67 | 2.5 s | 12.9 s | 6.7 |

Doğruluk, doğru sınıflanan uçuşların oranı. Kesinlik, verilen alarmların ne
kadarının gerçekten bir arızaya ait olduğunu, duyarlılık ise arızalı
uçuşların ne kadarının yakalandığını gösteriyor. Model basit yönteme göre
arızaları daha çok ve daha erken yakalıyor, yanlış alarmları da yarıya
indiriyor.

Arıza tiplerine göre bakınca durum şöyle:

| arıza tipi | yakalanan | ortanca tespit süresi |
|---|---|---|
| motor durması | 18 / 23 | 1.9 s |
| rudder takılması | 3 / 3 | 1.6 s |
| elevator takılması | 2 / 2 | 5.7 s |
| aileron takılması | 1 / 8 | 12.9 s |

Arızasız 10 uçuşun birinde yanlış alarm var. Ayrıca 4 motor uçuşunda ve 1
aileron uçuşunda alarm, arıza başlamadan önce veriliyor. Uçuş uçuş bütün
sonuçlar [docs/sonuclar.md](docs/sonuclar.md) dosyasında.

## Karşılaştığım sorunlar

Veriyi incelerken arızanın bazı sinyallere doğrudan yansıdığını gördüm.
ALFA'da arıza, ilgili motorun ya da servonun çıkış sinyali sabit bir değere
kilitlenerek oluşturulmuş. Bu yüzden arızadan kısa bir süre sonra `rc-out`
kaydındaki ilgili kanal tamamen donuyor. Sadece "bir kanal 6 saniyedir
değişmiyorsa alarm ver" diyen bir kural 0,98 doğruluk alıyor. Ama bu gerçek
bir tespit değil, arızanın uygulandığı yeri okumak demek. Bu yüzden bu
sinyalleri modelde hiç kullanmadım. Ayrıntıları
[docs/sizinti.md](docs/sizinti.md) dosyasına yazdım.

Kayıtlar otonom moda geçişle başlıyor ve otopilot ilk 15 saniyede hızı
yaklaşık 23 m/s'den 13 m/s'ye düşürüyor. İvmeölçerde bu yavaşlama motorun
durmasına çok benziyor. Bu yüzden ilk 15 saniyede alarm vermiyorum ve bu
kısmı eğitime de katmıyorum. En erken arıza 49,1. saniyede başladığı için bu
hiçbir arızayı gizlemiyor. Bu süreyi 5 saniye yapınca doğruluk 0,63'e
düşüyor. 20 saniye yapınca 0,76'ya çıkıyor, ama süreyi test sonuçlarına
bakarak seçmek sonucu olduğundan iyi gösterirdi; o yüzden fiziksel nedene
dayanan 15 saniyede bıraktım.

Aileron arızaları modelin en zayıf olduğu yer. Bir aileron takıldığında uçak
diğer aileron ve rudder ile yatmaya devam ediyor, sadece biraz daha yavaş.
Uçak düz uçarken bu neredeyse hiç iz bırakmıyor ve fark ancak otopilot
belirgin bir dönüş istediğinde ortaya çıkıyor.

Bunların dışında birkaç küçük durumla daha karşılaştım. Adında `emr_traj`
geçen 17 uçuşta, arızadan 0,04-0,09 saniye sonra uçağa yeni bir acil durum
rotası veriliyor. Bu kadar kısa bir süre, rotayı arızayı uygulayan sistemin
başlattığını gösteriyor, bu yüzden bu uçuşların sonuçlarını ayrıca
gösterdim. 34 uçuşta hava hızı sensörü hep 0 okuyor, bu yüzden hız için
navigasyon sisteminin hesapladığı hızı kullandım. Ölçülen yatış ve pitch
açıları ise saniyede 20 kez yayınlansa da aslında saniyede sadece 2,5 kez
değişiyor.

## C kodu

Modelin C hâli `c/alfa_tespit.h` ve `c/alfa_tespit.c` dosyalarında. Kod
dinamik bellek kullanmıyor ve 32 bitlik kayan nokta sayılarla çalışıyor.
Her yeni ölçümde `alfa_adim()` fonksiyonu bir kez çağrılıyor. Son 3
saniyenin artıkları bir halka tamponda tutuluyor ve ortalamalar bu tampondan
hesaplanıyor. Eğitilmiş katsayılar `c/alfa_param.c` dosyasında duruyor. Bu
dosyayı elle yazmadım; `c_dogrula.py` modeli eğittikten sonra otomatik
oluşturuyor.

```c
static alfa_durum_t dedektor;

alfa_baslat(&dedektor, &ALFA_PARAM);

/* saniyede 10 kez */
alfa_cikti_t c = alfa_adim(&dedektor, &girdi);
if (c.alarm) {
    /* arıza var */
}
```

Bir sensör bozuk bir değer (NaN ya da sonsuz) gönderirse o ölçüm atlanıyor
ve dedektörün durumu değişmiyor. Cortex-M4 için derlendiğinde kod 1072
bayt, katsayılar 180 bayt yer kaplıyor ve çalışırken 648 bayt RAM
kullanıyor. Gerçek bir kartta çalışma süresini henüz ölçmedim.

C kodunu kontrol etmek için 47 uçuşun hepsini hem Python'dan hem C'den
geçirdim. Her uçuşta alarm aynı anda verildi ve iki skor arasındaki en büyük
fark milyonda 3 civarında kaldı. Bu küçük fark, C'nin 32 bit, Python'un 64
bit sayılarla hesap yapmasından geliyor
([docs/c_dogrulama.md](docs/c_dogrulama.md)).

## Çalıştırma

Python 3.11 ya da daha yeni bir sürüm, C tarafı için de gcc ve make
gerekiyor. Cortex-M4 kod boyutunu görmek için `arm-none-eabi-gcc` de lazım.

```
pip install -r requirements.txt
python -m pytest          # testler
python karsilastir.py     # sonuçları ve grafiği üretir (yaklaşık 3 dakika)
python c_dogrula.py       # C katsayılarını üretir ve C'yi Python ile karşılaştırır
make -C c                 # C kodunu derler
make -C c arm             # Cortex-M4 için kod boyutu
```

Sızıntı testi `rc-out` kaydına baktığı için ham veriye ihtiyaç duyuyor:

```
python veri_indir.py
python sizinti.py
```

GitHub'a her gönderimde testler çalışıyor, C kodu derleniyor ve
`docs/sonuclar.md` baştan üretilip repodaki hâliyle karşılaştırılıyor.

## Eksikler ve sonraki adımlar

Veri seti küçük. 46 uçuşta tek bir uçuşun sonucu bile doğruluğu yaklaşık 2
puan değiştirebiliyor, bu yüzden sonuçları yaklaşık değerler olarak görmek
gerekiyor. Saatte 6,7 yanlış alarm gerçek bir uçak için hâlâ fazla.
Veri setindeki arızasız uçuş süresi toplam 54 dakika civarında; yanlış alarm
oranını güvenilir şekilde ölçmek için çok daha uzun kayıt gerekiyor.

Model şu an sadece bir arıza olup olmadığını söylüyor, hangi arıza olduğunu
söylemiyor. Sıradaki adımlarım C kodunu gerçek bir STM32 kartında çalıştırıp
süresini ölçmek, aileron arızaları için daha iyi bir yol bulmak ve arıza
tipini de söyleyen bir model denemek.

## Kaynaklar

A. Keipour, M. Mousaei, S. Scherer, "ALFA: A Dataset for UAV Fault and
Anomaly Detection", The International Journal of Robotics Research,
40(2-3):515-520, 2021.
[doi:10.1177/0278364920966642](https://doi.org/10.1177/0278364920966642)

A. Keipour, M. Mousaei, S. Scherer, "ALFA: AIR Lab Failure and Anomaly
Dataset", Carnegie Mellon University, KiltHub, 2020.
[doi:10.1184/R1/12707963.v1](https://doi.org/10.1184/R1/12707963.v1).
Veri setinin lisansı CC BY 4.0; `veri/hizali/` ve `tests/ornek/` altındaki
dosyalar bu veriden türetildi.

---

Büşra Şen · İstanbul Medipol Üniversitesi, Yönetim Bilişim Sistemleri
