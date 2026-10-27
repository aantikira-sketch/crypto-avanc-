#include <stdint.h>
#include <windows.h>
#include "kyberslash.c"

typedef uint32_t (*fn_t)(uint32_t);
static fn_t FN[4] = { msg_div, msg_fix, comp4_div, comp4_fix };

/* Retourne le temps moyen (ns) par appel sur un lot de n entrées. */
EXPORT double bench(int which, const uint32_t *in, int n) {
    LARGE_INTEGER f, a, b;
    volatile uint32_t sink = 0;
    fn_t fn = FN[which];
    QueryPerformanceFrequency(&f);
    QueryPerformanceCounter(&a);
    for (int i = 0; i < n; i++) sink += fn(in[i]);
    QueryPerformanceCounter(&b);
    return (double)(b.QuadPart - a.QuadPart) * 1e9 / (double)f.QuadPart / n;
}