/*
 * KyberSlash : versions avec division (_div) et corrigees (_fix).
 * Compilation : python -m ziglang cc -O0 -shared -o timing\kyberslash.dll timing\kyberslash.c
 * IMPORTANT : compiler en -O0 (ou -O1). En -O2/-O3 le compilateur transforme la
 * division par la constante Q en multiplication, et la fuite disparait.
 * Domaine : t doit etre dans [0, Q-1] (verifie exhaustivement par check_c.py).
 */
#include <stdint.h>
#define Q 3329

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif

/* d = 1 : poly_tomsg (déchiffrement). Division par Q sur une valeur dépendant du secret. */
EXPORT uint32_t msg_div(uint32_t t) { return (((t << 1) + Q/2) / Q) & 1; }
EXPORT uint32_t msg_fix(uint32_t t) { t <<= 1; t += 1665; t *= 80635; t >>= 28; return t & 1; }

/* d = 4 : compression (d_v de ML-KEM-512/768). */
EXPORT uint32_t comp4_div(uint32_t t) { return (((t << 4) + Q/2) / Q) & 15; }
EXPORT uint32_t comp4_fix(uint32_t t) { t <<= 4; t += 1665; t *= 80635; t >>= 28; return t & 15; }
/* Le produit (t<<4 + 1665) * 80635 atteint ~1,03 * 2^32 : il deborde en 32 bits.
 * Sans effet : apres >> 28 seuls 4 bits utiles restent, et & 15 supprime le reste.
 * Verifie par check_c.py et test_m4.py, qui executent ce code C reel. */