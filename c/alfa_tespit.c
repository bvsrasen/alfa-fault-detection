#include "alfa_tespit.h"

#include <math.h>
#include <string.h>

#define G 9.80665f
#define DERECE (3.14159265f / 180.0f)

/* Normalize artık bundan büyükse fiziksel değil, bozuk girdi demek
 * (gerçek uçuşlarda en büyüğü ~20). */
#define Z_SINIR 1000.0f

int alfa_baslat(alfa_durum_t *d, const alfa_param_t *prm)
{
    memset(d, 0, sizeof(*d));
    d->prm = prm;
    if (!prm)
        return -1;
    for (int k = 0; k < ALFA_KANAL; k++)
        if (!(prm->sigma[k] > 0.0f))
            return -1;
    return 0;
}

/* 5 kanalın normalize artıkları (Python'da ArtikModeli.z). Bozuk girdide 0 döner. */
static int artiklar(const alfa_param_t *p, const alfa_girdi_t *g, float z[ALFA_KANAL])
{
    float V = sqrtf(g->vn * g->vn + g->ve * g->ve + g->vd * g->vd);
    float hiz_hata = g->hiz_hata / 100.0f;
    float donus_r = G * tanf(g->roll * DERECE) / fmaxf(V, 5.0f);

    float ax = p->w_ax[0] + p->w_ax[1] * g->alt_hata + p->w_ax[2] * hiz_hata + p->w_ax[3] * g->pitch;
    float ay = p->w_ay[0];
    float pp = p->w_p[0] + p->w_p[1] * (g->roll_k - g->roll);
    float q = p->w_q[0] + p->w_q[1] * (g->pitch_k - g->pitch) + p->w_q[2] * g->roll * g->roll;
    float r = p->w_r[0] + p->w_r[1] * donus_r;

    z[0] = (g->ax - ax) / p->sigma[0];
    z[1] = (g->ay - ay) / p->sigma[1];
    z[2] = (g->p - pp) / p->sigma[2];
    z[3] = (g->q - q) / p->sigma[3];
    z[4] = (g->r - r) / p->sigma[4];

    for (int k = 0; k < ALFA_KANAL; k++)
        if (!(fabsf(z[k]) < Z_SINIR)) /* NaN da buraya düşer */
            return 0;
    return 1;
}

alfa_cikti_t alfa_adim(alfa_durum_t *d, const alfa_girdi_t *g)
{
    const alfa_param_t *p = d->prm;
    alfa_cikti_t c = { NAN, -INFINITY, d->alarm, 0 };

    float z[ALFA_KANAL];
    if (!artiklar(p, g, z)) {
        c.gecersiz = 1;
        return c;
    }

    /* Artığı halka tampona yaz */
    d->i_z = (d->i_z + 1) % ALFA_PENCERE;
    memcpy(d->z[d->i_z], z, sizeof(z));
    if (d->n_z < ALFA_PENCERE)
        d->n_z++;

    /* Son 1 s ve 3 s ortalamaları; başta pencere dolmadıysa eldeki örneklerle */
    int n_uzun = d->n_z;
    int n_kisa = n_uzun < ALFA_KISA ? n_uzun : ALFA_KISA;
    float ort_uzun[ALFA_KANAL] = { 0 }, ort_kisa[ALFA_KANAL] = { 0 }, std_kisa[ALFA_KANAL] = { 0 };
    for (int i = 0; i < n_uzun; i++) {
        const float *zi = d->z[(d->i_z + ALFA_PENCERE - i) % ALFA_PENCERE];
        for (int k = 0; k < ALFA_KANAL; k++) {
            ort_uzun[k] += zi[k];
            if (i < n_kisa)
                ort_kisa[k] += zi[k];
        }
    }
    for (int k = 0; k < ALFA_KANAL; k++) {
        ort_uzun[k] /= (float)n_uzun;
        ort_kisa[k] /= (float)n_kisa;
    }

    /* Son 1 s'nin standart sapması (n-1 ile, pandas'taki gibi) */
    if (n_kisa >= 2) {
        for (int i = 0; i < n_kisa; i++) {
            const float *zi = d->z[(d->i_z + ALFA_PENCERE - i) % ALFA_PENCERE];
            for (int k = 0; k < ALFA_KANAL; k++) {
                float e = zi[k] - ort_kisa[k];
                std_kisa[k] += e * e;
            }
        }
        for (int k = 0; k < ALFA_KANAL; k++)
            std_kisa[k] = sqrtf(std_kisa[k] / (float)(n_kisa - 1));
    }

    /* Öznitelik sırası Python'daki Lojistik.ozellikler ile aynı */
    float logit = p->lr_b;
    for (int k = 0; k < ALFA_KANAL; k++) {
        logit += p->lr_w[k] * z[k];
        logit += p->lr_w[ALFA_KANAL + k] * fabsf(z[k]);
        logit += p->lr_w[2 * ALFA_KANAL + k] * ort_kisa[k];
        logit += p->lr_w[3 * ALFA_KANAL + k] * ort_uzun[k];
        logit += p->lr_w[4 * ALFA_KANAL + k] * std_kisa[k];
    }
    c.logit = logit;

    /* Son 5 logit'in en küçüğü eşiği geçerse alarm */
    d->i_logit = (d->i_logit + 1) % ALFA_KALICI;
    d->logit[d->i_logit] = logit;
    if (d->n_logit < ALFA_KALICI)
        d->n_logit++;
    if (d->n_logit == ALFA_KALICI && g->t >= p->isinma_s) {
        float en_kucuk = d->logit[0];
        for (int i = 1; i < ALFA_KALICI; i++)
            en_kucuk = fminf(en_kucuk, d->logit[i]);
        c.skor = en_kucuk;
        if (en_kucuk > p->esik)
            d->alarm = 1;
    }
    c.alarm = d->alarm;
    return c;
}
