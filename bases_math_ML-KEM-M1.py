"""
===============================================================
PROJET ML-KEM — MEMBRE 1
Opérations polynomiales, NTT, NTT inverse et tests
===============================================================

Paramètres ML-KEM :
    N = 256
    Q = 3329
    ZETA = 17

Le polynôme est représenté par une liste de 256 coefficients.
Les coefficients sont calculés modulo Q.

Ce code est pédagogique. Les tests vérifient la cohérence
arithmétique, mais ne remplacent pas une validation complète
contre les vecteurs de test officiels de FIPS 203.
===============================================================
"""

import random

# =============================================================
# 1. PARAMÈTRES
# =============================================================

N = 256
Q = 3329
ZETA = 17

# Inverse de 128 modulo Q :
# (128 * 3303) % 3329 == 1
INV_128 = 3303


# =============================================================
# 2. VALIDATION ET AFFICHAGE DES POLYNÔMES
# =============================================================

def verifier_polynome(f):
    """Vérifie qu'un polynôme contient exactement 256 coefficients."""
    if len(f) != N:
        raise ValueError("Un polynôme ML-KEM doit avoir 256 coefficients.")


def afficher_polynome(f, nombre=8):
    """Affiche les premiers coefficients d'un polynôme."""
    verifier_polynome(f)
    print(f[:nombre])


# =============================================================
# 3. ADDITION ET SOUSTRACTION
# =============================================================

def poly_add(f, g):
    """
    Addition coefficient par coefficient modulo Q.

    Exemple :
        (1 + 2X) + (3 + 4X) = 4 + 6X
    """
    verifier_polynome(f)
    verifier_polynome(g)

    return [(f[i] + g[i]) % Q for i in range(N)]


def poly_sub(f, g):
    """
    Soustraction coefficient par coefficient modulo Q.
    """
    verifier_polynome(f)
    verifier_polynome(g)

    return [(f[i] - g[i]) % Q for i in range(N)]


# =============================================================
# 4. MULTIPLICATION NAÏVE : RÉFÉRENCE POUR LES TESTS
# =============================================================

def poly_mul_naive(f, g):
    """
    Multiplie deux polynômes dans :

        Rq = Zq[X] / (X^256 + 1)

    La relation X^256 = -1 implique que :
        X^(256+k) = -X^k

    Cette fonction est simple à comprendre, mais elle demande
    O(N²) opérations.
    """
    verifier_polynome(f)
    verifier_polynome(g)

    resultat = [0] * N

    for i in range(N):
        for j in range(N):
            produit = f[i] * g[j]
            degre = i + j

            if degre < N:
                resultat[degre] += produit
            else:
                resultat[degre - N] -= produit

    return [x % Q for x in resultat]


# =============================================================
# 5. BITREV7 : INVERSION DES 7 BITS
# =============================================================

def bitrev7(i):
    """
    Inverse les 7 bits de i.

    Cette fonction permet de calculer l'ordre des exposants
    utilisés dans les constantes de la NTT.
    """
    if not 0 <= i < 128:
        raise ValueError("i doit être compris entre 0 et 127.")

    resultat = 0

    for _ in range(7):
        resultat = (resultat << 1) | (i & 1)
        i >>= 1

    return resultat


# =============================================================
# 6. CONSTANTES ZETAS
# =============================================================

# zetas[i] = 17^(BitRev7(i)) modulo 3329.
#
# L'entrée d'indice 0 vaut 1.
# Les algorithmes NTT et NTT inverse utilisent les indices
# de 1 à 127 selon leur ordre de parcours.

ZETAS = [
    pow(ZETA, bitrev7(i), Q)
    for i in range(128)
]


# =============================================================
# 7. NTT DIRECTE
# =============================================================

def ntt(f):
    """
    Transforme un polynôme en sa représentation NTT ML-KEM.

    La transformation comporte 7 couches :
        128, 64, 32, 16, 8, 4, 2

    La représentation finale est organisée en 128 paires
    de coefficients, correspondant à des polynômes de degré 1.
    """
    verifier_polynome(f)

    r = [x % Q for x in f]

    k = 1
    longueur = 128

    while longueur >= 2:

        for debut in range(0, N, 2 * longueur):

            zeta = ZETAS[k]
            k += 1

            for j in range(debut, debut + longueur):

                # Multiplication modulo Q
                t = (zeta * r[j + longueur]) % Q

                # Papillon NTT
                r[j + longueur] = (r[j] - t) % Q
                r[j] = (r[j] + t) % Q

        longueur //= 2

    return r


# =============================================================
# 8. NTT INVERSE
# =============================================================

def ntt_inverse(f_hat):
    """
    Transforme la représentation NTT en coefficients du
    polynôme initial.

    La dernière étape multiplie chaque coefficient par
    l'inverse de 128 modulo Q, soit 3303.
    """
    verifier_polynome(f_hat)

    r = [x % Q for x in f_hat]

    k = 127
    longueur = 2

    while longueur <= 128:

        for debut in range(0, N, 2 * longueur):

            zeta = ZETAS[k]
            k -= 1

            for j in range(debut, debut + longueur):

                t = r[j]

                r[j] = (t + r[j + longueur]) % Q

                r[j + longueur] = (
                    zeta * (r[j + longueur] - t)
                ) % Q

        longueur *= 2

    # Normalisation de la transformation inverse
    return [(x * INV_128) % Q for x in r]


# =============================================================
# 9. BASE CASE MULTIPLY
# =============================================================

def base_case_multiply(a0, a1, b0, b1, gamma):
    """
    Multiplie deux polynômes de degré 1 :

        A(X) = a0 + a1*X
        B(X) = b0 + b1*X

    dans l'anneau défini par :

        X² = gamma

    Le résultat est :
        c0 = a0*b0 + gamma*a1*b1
        c1 = a0*b1 + a1*b0
    """
    c0 = (a0 * b0 + gamma * a1 * b1) % Q
    c1 = (a0 * b1 + a1 * b0) % Q

    return [c0, c1]


# =============================================================
# 10. MULTIPLICATION DANS LE DOMAINE NTT
# =============================================================

def multiply_ntts(f_hat, g_hat):
    """
    Multiplication dans le domaine NTT selon FIPS 203,
    algorithme 11.

    Chaque paire de coefficients est multipliée avec
    gamma_i = 17^(2*BitRev7(i)+1) modulo Q.
    """
    verifier_polynome(f_hat)
    verifier_polynome(g_hat)

    resultat = [0] * N

    for i in range(128):
        gamma = pow(ZETA, 2 * bitrev7(i) + 1, Q)

        resultat[2 * i:2 * i + 2] = base_case_multiply(
            f_hat[2 * i],
            f_hat[2 * i + 1],
            g_hat[2 * i],
            g_hat[2 * i + 1],
            gamma
        )

    return resultat

# =============================================================
# 11. MULTIPLICATION AVEC NTT
# =============================================================

def poly_mul_ntt(f, g):
    """
    Multiplie deux polynômes grâce à la NTT :

        1. NTT(f)
        2. NTT(g)
        3. Multiplication des représentations NTT
        4. NTT inverse du résultat
    """
    verifier_polynome(f)
    verifier_polynome(g)

    f_hat = ntt(f)
    g_hat = ntt(g)

    produit_hat = multiply_ntts(f_hat, g_hat)

    return ntt_inverse(produit_hat)


# =============================================================
# 12. TESTS AUTOMATIQUES
# =============================================================

def lancer_tests():
    """Exécute les tests de cohérence du module."""

    print("=" * 60)
    print("TESTS DU MODULE POLYNOMIAL ML-KEM")
    print("=" * 60)

    rng = random.Random(2026)

    # ---------------------------------------------------------
    # Test 1 : paramètres et constantes
    # ---------------------------------------------------------
    assert N == 256
    assert Q == 3329
    assert pow(ZETA, 128, Q) == Q - 1
    assert (128 * INV_128) % Q == 1
    assert ZETAS[0] == 1

    print("[OK] Paramètres et constantes")

    # ---------------------------------------------------------
    # Test 2 : addition et soustraction
    # ---------------------------------------------------------
    f = [0] * N
    g = [0] * N

    f[0], f[1] = 1, 2
    g[0], g[1] = 3, 4

    assert poly_add(f, g)[:4] == [4, 6, 0, 0]
    assert poly_sub(f, g)[:4] == [Q - 2, Q - 2, 0, 0]

    print("[OK] Addition et soustraction")

    # ---------------------------------------------------------
    # Test 3 : multiplication naïve
    # ---------------------------------------------------------
    assert poly_mul_naive(f, g)[:4] == [3, 10, 8, 0]

    print("[OK] Multiplication naïve")

    # ---------------------------------------------------------
    # Test 4 : relation X^256 = -1
    # ---------------------------------------------------------
    x255 = [0] * N
    x = [0] * N

    x255[255] = 1
    x[1] = 1

    resultat = poly_mul_naive(x255, x)

    assert resultat[0] == Q - 1
    assert all(resultat[i] == 0 for i in range(1, N))

    print("[OK] Relation X^256 = -1")

    # ---------------------------------------------------------
    # Test 5 : NTT suivie de la NTT inverse
    # ---------------------------------------------------------
    for _ in range(5):
        p = [rng.randrange(Q) for _ in range(N)]
        assert ntt_inverse(ntt(p)) == p

    print("[OK] NTT inverse de la NTT")

    # ---------------------------------------------------------
    # Test 6 : BaseCaseMultiply
    # ---------------------------------------------------------
    # (1 + 2X)(3 + 4X), avec X² = 5
    resultat = base_case_multiply(1, 2, 3, 4, 5)

    assert resultat == [(3 + 2*4*5) % Q, (1*4 + 2*3) % Q]

    print("[OK] BaseCaseMultiply")

    # ---------------------------------------------------------
    # Test 7 : multiplication NTT vs multiplication naïve
    # ---------------------------------------------------------
    for _ in range(5):
        a = [rng.randrange(Q) for _ in range(N)]
        b = [rng.randrange(Q) for _ in range(N)]

        attendu = poly_mul_naive(a, b)
        obtenu = poly_mul_ntt(a, b)

        assert obtenu == attendu

    print("[OK] Multiplication NTT = multiplication naïve")

    # ---------------------------------------------------------
    # Test 8 : multiplication d'un exemple simple
    # ---------------------------------------------------------
    resultat = poly_mul_ntt(f, g)

    assert resultat[:4] == [3, 10, 8, 0]

    print("[OK] Exemple (1 + 2X)(3 + 4X)")

    print("=" * 60)
    print("TOUS LES TESTS ONT RÉUSSI")
    print("=" * 60)


# =============================================================
# 13. POINT D'ENTRÉE DU PROGRAMME
# =============================================================

if __name__ == "__main__":
    lancer_tests()
