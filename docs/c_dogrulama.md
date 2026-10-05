# C dedektörünün doğrulanması

`python c_dogrula.py` ile üretildi.

Model 46 etiketli uçuşun hepsiyle eğitildi (eşik 1.7219) ve
`c/alfa_param.c` olarak yazıldı. Sonra 47 uçuşun hepsi (etiketsiz olan
dahil) hem Python'dan hem derlenmiş C kodundan geçirildi.

- Alarm anı aynı olan uçuş: 47 / 47

C 32 bitlik, Python 64 bitlik kayan nokta sayılarla hesaplıyor; aradaki
küçük farklar bu yüzden. Bu tablo bir başarı ölçüsü değil (model bu
uçuşlarla eğitildi), sadece iki kodun aynı şeyi hesapladığının kontrolü.

| uçuş | örnek | maks_logit_farkı | maks_skor_farkı | alarm_py | alarm_c | alarm_aynı |
|---|---|---|---|---|---|---|
| 2018-07-18-12-10-11_no_ground_truth | 2051 | 1.8e-06 | 1.8e-06 | 15.2 | 15.2 | True |
| 2018-07-18-15-53-31_1_engine_failure | 1322 | 2.4e-06 | 1.4e-06 | 119.7 | 119.7 | True |
| 2018-07-18-15-53-31_2_engine_failure | 887 | 1.3e-06 | 1.0e-06 | 76.2 | 76.2 | True |
| 2018-07-18-16-22-01_engine_failure_with_emr_traj | 1323 | 2.2e-06 | 1.4e-06 | 51.0 | 51.0 | True |
| 2018-07-18-16-37-39_1_no_failure | 303 | 1.4e-06 | 1.4e-06 | - | - | True |
| 2018-07-18-16-37-39_2_engine_failure_with_emr_traj | 1302 | 1.5e-06 | 1.5e-06 | 114.6 | 114.6 | True |
| 2018-07-30-16-29-45_engine_failure_with_emr_traj | 1420 | 1.4e-06 | 1.2e-06 | 125.2 | 125.2 | True |
| 2018-07-30-16-39-00_1_engine_failure | 1315 | 1.5e-06 | 1.5e-06 | 118.7 | 118.7 | True |
| 2018-07-30-16-39-00_2_engine_failure | 1060 | 2.3e-06 | 2.0e-06 | 72.6 | 72.6 | True |
| 2018-07-30-16-39-00_3_no_failure | 790 | 2.8e-06 | 8.9e-07 | - | - | True |
| 2018-07-30-17-10-45_engine_failure_with_emr_traj | 1328 | 1.6e-06 | 1.1e-06 | 36.4 | 36.4 | True |
| 2018-07-30-17-20-01_engine_failure_with_emr_traj | 1064 | 1.4e-06 | 1.3e-06 | 88.3 | 88.3 | True |
| 2018-07-30-17-36-35_engine_failure_with_emr_traj | 1566 | 2.2e-06 | 1.3e-06 | 135.5 | 135.5 | True |
| 2018-07-30-17-46-31_engine_failure_with_emr_traj | 1123 | 1.6e-06 | 1.1e-06 | 92.5 | 92.5 | True |
| 2018-09-11-11-56-30_engine_failure | 1243 | 2.3e-06 | 1.1e-06 | 105.5 | 105.5 | True |
| 2018-09-11-14-16-55_no_failure | 333 | 1.1e-06 | 1.1e-06 | - | - | True |
| 2018-09-11-14-22-07_1_engine_failure | 1141 | 1.5e-06 | 1.1e-06 | 105.3 | 105.3 | True |
| 2018-09-11-14-22-07_2_engine_failure | 622 | 1.6e-06 | 1.1e-06 | 15.0 | 15.0 | True |
| 2018-09-11-14-41-38_no_failure | 432 | 1.2e-06 | 1.1e-06 | - | - | True |
| 2018-09-11-14-41-51_elevator_failure | 1283 | 1.7e-06 | 1.3e-06 | 119.8 | 119.8 | True |
| 2018-09-11-14-52-54_left_aileron__right_aileron__failure | 2332 | 1.7e-06 | 1.0e-06 | 17.2 | 17.2 | True |
| 2018-09-11-15-05-11_1_elevator_failure | 759 | 1.7e-06 | 1.7e-06 | 73.1 | 73.1 | True |
| 2018-09-11-15-05-11_2_no_failure | 673 | 1.1e-06 | 1.1e-06 | 58.9 | 58.9 | True |
| 2018-09-11-15-06-34_1_rudder_right_failure | 701 | 1.9e-06 | 1.9e-06 | 56.2 | 56.2 | True |
| 2018-09-11-15-06-34_2_rudder_right_failure | 691 | 2.8e-06 | 2.7e-06 | 52.5 | 52.5 | True |
| 2018-09-11-15-06-34_3_rudder_left_failure | 692 | 2.9e-06 | 2.9e-06 | 60.7 | 60.7 | True |
| 2018-09-11-17-27-13_1_rudder_zero__left_aileron_failure | 1433 | 1.2e-06 | 1.1e-06 | 132.1 | 132.1 | True |
| 2018-09-11-17-27-13_2_both_ailerons_failure | 1015 | 3.3e-06 | 2.9e-06 | 78.1 | 78.1 | True |
| 2018-09-11-17-55-30_1_right_aileron_failure | 1329 | 1.3e-06 | 9.4e-07 | - | - | True |
| 2018-09-11-17-55-30_2_left_aileron_failure | 813 | 9.6e-07 | 9.4e-07 | - | - | True |
| 2018-10-05-14-34-20_1_no_failure | 667 | 1.2e-06 | 1.0e-06 | - | - | True |
| 2018-10-05-14-34-20_2_right_aileron_failure_with_emr_traj | 1621 | 1.6e-06 | 1.6e-06 | - | - | True |
| 2018-10-05-14-37-22_1_no_failure | 725 | 1.4e-06 | 1.0e-06 | 17.3 | 17.3 | True |
| 2018-10-05-14-37-22_2_right_aileron_failure | 1448 | 1.7e-06 | 9.5e-07 | 91.7 | 91.7 | True |
| 2018-10-05-14-37-22_3_left_aileron_failure | 964 | 1.4e-06 | 8.5e-07 | - | - | True |
| 2018-10-05-15-52-12_1_no_failure | 895 | 2.1e-06 | 1.2e-06 | - | - | True |
| 2018-10-05-15-52-12_2_no_failure | 483 | 1.8e-06 | 1.2e-06 | - | - | True |
| 2018-10-05-15-52-12_3_engine_failure_with_emr_traj | 665 | 1.5e-06 | 1.2e-06 | 51.3 | 51.3 | True |
| 2018-10-05-15-55-10_engine_failure_with_emr_traj | 1130 | 1.5e-06 | 1.1e-06 | 101.4 | 101.4 | True |
| 2018-10-05-16-04-46_engine_failure_with_emr_traj | 920 | 9.9e-07 | 9.9e-07 | 77.0 | 77.0 | True |
| 2018-10-18-11-03-57_engine_failure_with_emr_traj | 1163 | 1.9e-06 | 1.3e-06 | 108.0 | 108.0 | True |
| 2018-10-18-11-04-00_engine_failure_with_emr_traj | 1224 | 1.4e-06 | 1.4e-06 | 111.7 | 111.7 | True |
| 2018-10-18-11-04-08_1_engine_failure_with_emr_traj | 1145 | 2.2e-06 | 2.1e-06 | 101.0 | 101.0 | True |
| 2018-10-18-11-04-08_2_engine_failure_with_emr_traj | 1177 | 1.2e-06 | 1.1e-06 | 101.0 | 101.0 | True |
| 2018-10-18-11-04-35_engine_failure_with_emr_traj | 1090 | 1.7e-06 | 1.7e-06 | 102.6 | 102.6 | True |
| 2018-10-18-11-06-06_engine_failure_with_emr_traj | 1164 | 1.6e-06 | 1.5e-06 | 104.8 | 104.8 | True |
| 2018-10-18-11-08-24_no_failure | 263 | 1.1e-06 | 5.7e-07 | - | - | True |

## Bellek ve kod boyutu

```
sizeof(alfa_durum_t) = 648 bayt
sizeof(alfa_param_t) = 180 bayt
```

Cortex-M4F için (`make -C c arm`, `-Os`):

```
text	   data	    bss	    dec	    hex	filename
   1072	      0	      0	   1072	    430	build/alfa_tespit_m4.o
    180	      0	      0	    180	     b4	build/alfa_param_m4.o
```

`alfa_tespit_m4.o` kod, `alfa_param_m4.o` katsayılar (ikisi de Flash'ta).
RAM'de tek gereken `alfa_durum_t`.
