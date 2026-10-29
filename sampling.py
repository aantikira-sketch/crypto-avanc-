import hashlib

# Constantes ML-KEM
N = 256
Q = 3329


def PRF(seed: bytes, nonce: int, eta: int) -> bytes:
    """
    Fonction pseudo-aléatoire utilisée pour générer les octets
    nécessaires à SamplePolyCBD.

    seed : graine de 32 octets
    nonce : entier compris entre 0 et 255
    eta : paramètre de distribution (2 ou 3)
    """
    if len(seed) != 32:
        raise ValueError("La graine doit contenir 32 octets.")

    if not 0 <= nonce <= 255:
        raise ValueError("Le nonce doit être compris entre 0 et 255.")

    if eta not in (2, 3):
        raise ValueError("eta doit valoir 2 ou 3.")

    return hashlib.shake_256(
        seed + bytes([nonce])
    ).digest(64 * eta)


def SampleNTT(rho: bytes, j: int, i: int) -> list[int]:
    """
    Échantillonne un polynôme dans le domaine NTT
    à partir de rho et des indices j et i.
    """
    if len(rho) != 32:
        raise ValueError("rho doit contenir 32 octets.")

    if not 0 <= i <= 255 or not 0 <= j <= 255:
        raise ValueError("Les indices i et j doivent être des octets.")

    # SHAKE-128 est utilisé pour générer le flux d'octets.
    # On augmente sa longueur jusqu'à obtenir 256 coefficients valides.
    longueur = 1024
    while True:
        flux = hashlib.shake_128(
            rho + bytes([j, i])
        ).digest(longueur)

        coefficients = []

        for pos in range(0, len(flux) - 2, 3):
            b0 = flux[pos]
            b1 = flux[pos + 1]
            b2 = flux[pos + 2]

            d1 = b0 + 256 * (b1 & 0x0F)
            d2 = (b1 >> 4) + 16 * b2

            if d1 < Q:
                coefficients.append(d1)

            if d2 < Q:
                coefficients.append(d2)

            if len(coefficients) >= N:
                return coefficients[:N]

        longueur *= 2


def SamplePolyCBD(buf: bytes, eta: int) -> list[int]:
    """
    Génère un polynôme selon la distribution binomiale centrée
    (Centered Binomial Distribution, CBD).
    """
    if eta not in (2, 3):
        raise ValueError("eta doit valoir 2 ou 3.")

    if len(buf) != 64 * eta:
        raise ValueError(
            f"Pour eta={eta}, il faut exactement {64 * eta} octets."
        )

    # Conversion des octets en bits, du bit de poids faible
    # au bit de poids fort.
    bits = [
        (octet >> position) & 1
        for octet in buf
        for position in range(8)
    ]

    coefficients = []

    for n in range(N):
        debut = 2 * eta * n

        somme1 = sum(bits[debut:debut + eta])
        somme2 = sum(bits[debut + eta:debut + 2 * eta])

        coefficients.append((somme1 - somme2) % Q)

    return coefficients


# Alias en minuscules, pratiques pour les autres modules.
sample_ntt = SampleNTT
sample_poly_cbd = SamplePolyCBD
