"""
K-PKE : génération des clés, chiffrement et déchiffrement.
Implémentation pédagogique inspirée de FIPS 203.
"""

import hashlib

from params import ML_KEM_512
from sampling import PRF, SampleNTT, SamplePolyCBD
from encoding import ByteEncode, ByteDecode, Compress, Decompress
from poly import ntt, ntt_inverse, multiply_ntts, poly_add, poly_sub

N = 256
Q = 3329


def _G(data: bytes) -> tuple[bytes, bytes]:
    """Calcule SHA3-512 et sépare le résultat en deux chaînes de 32 octets."""
    digest = hashlib.sha3_512(data).digest()
    return digest[:32], digest[32:]


def _sample_noise(seed: bytes, nonce: int, eta: int) -> list[int]:
    """Génère un polynôme de bruit à partir d'une graine et d'un nonce."""
    return SamplePolyCBD(PRF(seed, nonce, eta), eta)


def _dot_ntt(a: list, b: list) -> list[int]:
    """Calcule le produit scalaire de deux vecteurs dans le domaine NTT."""
    if len(a) != len(b):
        raise ValueError("Les vecteurs doivent avoir la même longueur.")

    result = [0] * N

    for x, y in zip(a, b):
        product = multiply_ntts(x, y)
        result = [(u + v) % Q for u, v in zip(result, product)]

    return result


def _encode_poly_vector(vector: list) -> bytes:
    """Encode un vecteur de polynômes avec 12 bits par coefficient."""
    return b"".join(ByteEncode(12, poly) for poly in vector)


def _decode_poly_vector(data: bytes, k: int) -> list:
    """Décode un vecteur de k polynômes de 256 coefficients."""
    expected_size = 384 * k

    if len(data) != expected_size:
        raise ValueError(
            f"Taille invalide : {expected_size} octets attendus."
        )

    vector = []

    for i in range(k):
        chunk = data[i * 384:(i + 1) * 384]
        vector.append(ByteDecode(12, chunk))

    return vector


def k_pke_keygen(d: bytes, p=ML_KEM_512):
    """
    Génère la clé publique ek et la clé secrète dk du K-PKE.
    d doit contenir exactement 32 octets.
    """
    if len(d) != 32:
        raise ValueError("d doit contenir exactement 32 octets.")

    rho, sigma = _G(d + bytes([p.k]))

    # A_hat[i][j] = SampleNTT(rho, j, i).
    A_hat = [
        [SampleNTT(rho, j, i) for j in range(p.k)]
        for i in range(p.k)
    ]

    # Génération des secrets s et des erreurs e.
    nonce = 0
    s = []

    for _ in range(p.k):
        s.append(_sample_noise(sigma, nonce, p.eta1))
        nonce += 1

    e = []

    for _ in range(p.k):
        e.append(_sample_noise(sigma, nonce, p.eta1))
        nonce += 1

    s_hat = [ntt(poly) for poly in s]
    e_hat = [ntt(poly) for poly in e]

    # t_hat = A_hat * s_hat + e_hat.
    t_hat = []

    for i in range(p.k):
        product = _dot_ntt(A_hat[i], s_hat)
        t_hat.append(poly_add(product, e_hat[i]))

    ek = _encode_poly_vector(t_hat) + rho
    dk = _encode_poly_vector(s_hat)

    return ek, dk


def k_pke_encrypt(ek: bytes, m: bytes, r: bytes, p=ML_KEM_512):
    """
    Chiffre un message de 32 octets.

    ek : clé publique.
    m  : message.
    r  : graine de bruit de 32 octets.
    """
    if len(ek) != p.ek_size:
        raise ValueError("Taille invalide de la clé publique.")

    if len(m) != 32:
        raise ValueError("Le message m doit contenir 32 octets.")

    if len(r) != 32:
        raise ValueError("La graine r doit contenir 32 octets.")

    t_hat = _decode_poly_vector(ek[:p.dk_pke_size], p.k)
    rho = ek[p.dk_pke_size:]

    # Matrice transposée A_hat^T :
    # A_hat_T[i][j] = SampleNTT(rho, i, j).
    A_hat_T = [
        [SampleNTT(rho, i, j) for j in range(p.k)]
        for i in range(p.k)
    ]

    # Génération du bruit y, e1 et e2.
    nonce = 0
    y = []

    for _ in range(p.k):
        y.append(_sample_noise(r, nonce, p.eta1))
        nonce += 1

    e1 = []

    for _ in range(p.k):
        e1.append(_sample_noise(r, nonce, p.eta2))
        nonce += 1

    e2 = _sample_noise(r, nonce, p.eta2)

    y_hat = [ntt(poly) for poly in y]

    # u = NTT^-1(A^T * NTT(y)) + e1.
    u = []

    for i in range(p.k):
        product = _dot_ntt(A_hat_T[i], y_hat)
        u.append(poly_add(ntt_inverse(product), e1[i]))

    # v = NTT^-1(t^T * NTT(y)) + e2 + Decompress_1(m).
    product = _dot_ntt(t_hat, y_hat)
    v = ntt_inverse(product)

    message_poly = [
        Decompress(1, bit)
        for bit in ByteDecode(1, m)
    ]

    v = poly_add(v, e2)
    v = poly_add(v, message_poly)

    # Compression et encodage de u et v.
    c1 = b"".join(
        ByteEncode(
            p.du,
            [Compress(p.du, x) for x in poly]
        )
        for poly in u
    )

    c2 = ByteEncode(
        p.dv,
        [Compress(p.dv, x) for x in v]
    )

    return c1 + c2


def k_pke_decrypt(dk: bytes, c: bytes, p=ML_KEM_512):
    """
    Déchiffre un chiffré K-PKE et retourne un message de 32 octets.
    """
    if len(dk) != p.dk_pke_size:
        raise ValueError("Taille invalide de la clé secrète.")

    if len(c) != p.c_size:
        raise ValueError("Taille invalide du chiffré.")

    s_hat = _decode_poly_vector(dk, p.k)

    # Séparation des parties u et v.
    u_size = 32 * p.du * p.k
    c1 = c[:u_size]
    c2 = c[u_size:]

    # Décodage et décompression de u.
    u = []

    for i in range(p.k):
        start = i * 32 * p.du
        end = (i + 1) * 32 * p.du

        encoded = ByteDecode(p.du, c1[start:end])

        u.append([
            Decompress(p.du, x)
            for x in encoded
        ])

    # Décodage et décompression de v.
    encoded_v = ByteDecode(p.dv, c2)
    v = [Decompress(p.dv, x) for x in encoded_v]

    # w = v - NTT^-1(s^T * NTT(u)).
    u_hat = [ntt(poly) for poly in u]
    product = _dot_ntt(s_hat, u_hat)
    w = poly_sub(v, ntt_inverse(product))

    # Extraction du message.
    message_bits = [Compress(1, x) for x in w]

    return ByteEncode(1, message_bits)
