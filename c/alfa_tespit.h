/*
 * ALFA verisiyle eğitilmiş arıza dedektörü.
 *
 * Saniyede 10 kez alfa_adim() çağrılır. Dinamik bellek yok, bütün durum
 * alfa_durum_t içinde. Eğitilmiş katsayılar alfa_param.c'de; o dosyayı
 * c_dogrula.py üretiyor.
 *
 * Her adımda:
 *   1. 5 artık (ax, ay, p, q, r): ölçülen - beklenen, nominal std'ye bölünmüş
 *   2. her artık için anlık, mutlak, 1 s ve 3 s ortalama, 1 s std -> 25 öznitelik
 *   3. lojistik regresyon logit'i
 *   4. son 5 logit'in en küçüğü eşiği geçerse alarm (alarm bir kez verilince kalır)
 *
 * Girdilerden biri NaN ya da sonsuzsa o örnek atlanır, durum değişmez.
 */
#ifndef ALFA_TESPIT_H
#define ALFA_TESPIT_H

#define ALFA_KANAL 5        /* ax, ay, p, q, r */
#define ALFA_OZNITELIK 25   /* 5 kanal x 5 öznitelik */
#define ALFA_PENCERE 30     /* 3 s */
#define ALFA_KISA 10        /* 1 s */
#define ALFA_KALICI 5       /* 0,5 s */

typedef struct {
    float t;            /* s, kaydın başından */
    float p, q, r;      /* gövde açısal hızları, rad/s */
    float ax, ay;       /* ivmeölçer, m/s^2 */
    float roll_k, roll; /* komut / ölçülen, derece */
    float pitch_k, pitch;
    float vn, ve, vd;   /* NED hız, m/s */
    float alt_hata;     /* otopilot irtifa hatası, m */
    float hiz_hata;     /* otopilot hava hızı hatası, cm/s */
} alfa_girdi_t;

typedef struct {
    float w_ax[4];      /* sabit, alt_hata, hiz_hata (m/s), pitch */
    float w_ay[1];      /* sabit */
    float w_p[2];       /* sabit, roll hatası */
    float w_q[3];       /* sabit, pitch hatası, roll^2 */
    float w_r[2];       /* sabit, g tan(roll) / V */
    float sigma[ALFA_KANAL];
    float lr_w[ALFA_OZNITELIK]; /* öznitelik ölçeklemesi ağırlıklara katılmış */
    float lr_b;
    float esik;
    float isinma_s;     /* bu süreden önce alarm yok */
} alfa_param_t;

typedef struct {
    const alfa_param_t *prm;
    float z[ALFA_PENCERE][ALFA_KANAL]; /* son 3 s'nin artıkları, halka tampon */
    int i_z, n_z;                      /* son yazılan yer, dolu satır sayısı */
    float logit[ALFA_KALICI];
    int i_logit, n_logit;
    int alarm;
} alfa_durum_t;

typedef struct {
    float logit;
    float skor;   /* son 5 logit'in en küçüğü; henüz yoksa -INF */
    int alarm;
    int gecersiz; /* bu örnek bozuktu ve atlandı */
} alfa_cikti_t;

/* Parametreler geçersizse -1 döner */
int alfa_baslat(alfa_durum_t *d, const alfa_param_t *prm);
alfa_cikti_t alfa_adim(alfa_durum_t *d, const alfa_girdi_t *g);

/* Eğitilmiş katsayılar, alfa_param.c */
extern const alfa_param_t ALFA_PARAM;

#endif
