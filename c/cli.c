/*
 * Bilgisayarda test için: hizalanmış uçuş tablosunu stdin'den okur, her
 * satırı alfa_adim()'a verir, sonucu stdout'a yazar.
 *
 *   alfa_cli < ucus.csv > cikti.csv
 *   alfa_cli --bilgi      (yapıların boyutu)
 *
 * Girdi CSV'sinin sütunları alfa_girdi_t ile aynı sırada, ilk satır başlık.
 */
#include <stdio.h>
#include <string.h>

#include "alfa_tespit.h"

int main(int argc, char **argv)
{
    if (argc > 1 && strcmp(argv[1], "--bilgi") == 0) {
        printf("sizeof(alfa_durum_t) = %zu bayt\n", sizeof(alfa_durum_t));
        printf("sizeof(alfa_param_t) = %zu bayt\n", sizeof(alfa_param_t));
        return 0;
    }

    alfa_durum_t d;
    if (alfa_baslat(&d, &ALFA_PARAM) != 0) {
        fprintf(stderr, "parametreler geçersiz\n");
        return 1;
    }

    char satir[1024];
    if (!fgets(satir, sizeof(satir), stdin))
        return 1; /* başlık */
    puts("t,logit,skor,alarm");

    alfa_girdi_t g;
    while (fgets(satir, sizeof(satir), stdin)) {
        int n = sscanf(satir, "%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f",
                       &g.t, &g.p, &g.q, &g.r, &g.ax, &g.ay, &g.roll_k, &g.roll,
                       &g.pitch_k, &g.pitch, &g.vn, &g.ve, &g.vd, &g.alt_hata, &g.hiz_hata);
        if (n != 15) {
            fprintf(stderr, "bozuk satır: %s", satir);
            return 1;
        }
        alfa_cikti_t c = alfa_adim(&d, &g);
        printf("%.2f,%.9g,%.9g,%d\n", (double)g.t, (double)c.logit, (double)c.skor, c.alarm);
    }
    return 0;
}
