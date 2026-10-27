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