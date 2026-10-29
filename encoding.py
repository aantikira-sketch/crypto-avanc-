"""
Encodage, décodage, compression et décompression
des coefficients utilisés dans ML-KEM.
"""

N = 256
Q = 3329


def ByteEncode(d: int, f: list[int]) -> bytes:
    """Encode les coefficients f sur d bits chacun."""
    if not 1 <= d <= 12:
        raise ValueError("d doit être compris entre 1 et 12.")

    if any(not 0 <= x < (1 << d) for x in f):
        raise ValueError("Un coefficient ne tient pas sur d bits.")

    bits = []
    for x in f:
        bits.extend((x >> i) & 1 for i in range(d))

    resultat = bytearray()
    for i in range(0, len(bits), 8):
        octet = 0
        for j, bit in enumerate(bits[i:i + 8]):
            octet |= bit << j
        resultat.append(octet)

    return bytes(resultat)


def ByteDecode(d: int, b: bytes) -> list[int]:
    """Décode une suite d'octets en coefficients sur d bits."""
    if not 1 <= d <= 12:
        raise ValueError("d doit être compris entre 1 et 12.")

    bits = [
        (octet >> i) & 1
        for octet in b
        for i in range(8)
    ]

    if len(bits) % d != 0:
        raise ValueError("La longueur des données est invalide.")

    coefficients = []

    for i in range(0, len(bits), d):
        x = sum(bits[i + j] << j for j in range(d))
        coefficients.append(x)

    return coefficients


def Compress(d: int, x: int) -> int:
    """Compresse un coefficient modulo Q sur d bits."""
    if not 1 <= d <= 11:
        raise ValueError("d doit être compris entre 1 et 11.")

    x %= Q
    return (((1 << d) * x + Q // 2) // Q) % (1 << d)


def Decompress(d: int, y: int) -> int:
    """Décompresse un coefficient représenté sur d bits."""
    if not 1 <= d <= 11:
        raise ValueError("d doit être compris entre 1 et 11.")

    if not 0 <= y < (1 << d):
        raise ValueError("y ne tient pas sur d bits.")

    return (Q * y + (1 << (d - 1))) // (1 << d)


def compress_poly(d: int, coefficients: list[int]) -> list[int]:
    """Compresse tous les coefficients d'un polynôme."""
    return [Compress(d, x) for x in coefficients]


def decompress_poly(d: int, coefficients: list[int]) -> list[int]:
    """Décompresse tous les coefficients d'un polynôme."""
    return [Decompress(d, x) for x in coefficients]


# Noms alternatifs en minuscules pour faciliter l'intégration.
byte_encode = ByteEncode
byte_decode = ByteDecode
compress = Compress
decompress = Decompress
