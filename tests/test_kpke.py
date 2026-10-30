import hashlib


import pytest

from params import ML_KEM_512, ML_KEM_768, ML_KEM_1024
from kpke import k_pke_keygen, k_pke_encrypt, k_pke_decrypt


PARAMETERS = [ML_KEM_512, ML_KEM_768, ML_KEM_1024]


@pytest.mark.parametrize("p", PARAMETERS)
def test_key_sizes(p):
    d = bytes(range(32))

    ek, dk = k_pke_keygen(d, p)

    assert len(ek) == p.ek_size
    assert len(dk) == p.dk_pke_size


@pytest.mark.parametrize("p", PARAMETERS)
def test_encrypt_decrypt(p):
    d = bytes(range(32))
    m = bytes(range(32))
    r = bytes(range(32, 64))

    ek, dk = k_pke_keygen(d, p)
    c = k_pke_encrypt(ek, m, r, p)
    recovered = k_pke_decrypt(dk, c, p)

    assert len(c) == p.c_size
    assert recovered == m


@pytest.mark.parametrize("p", PARAMETERS)
def test_keygen_is_deterministic(p):
    d = bytes(range(32))

    ek1, dk1 = k_pke_keygen(d, p)
    ek2, dk2 = k_pke_keygen(d, p)

    assert ek1 == ek2
    assert dk1 == dk2


@pytest.mark.parametrize("p", PARAMETERS)
def test_encryption_is_deterministic(p):
    d = bytes(range(32))
    m = bytes(range(32))
    r = bytes(range(32, 64))

    ek, _ = k_pke_keygen(d, p)

    c1 = k_pke_encrypt(ek, m, r, p)
    c2 = k_pke_encrypt(ek, m, r, p)

    assert c1 == c2


def test_keygen_intermediate_values():
    """Vérifie rho, sigma et t_hat pour une graine fixe."""
    d = bytes(range(32))
    p = ML_KEM_512

    ek, _ = k_pke_keygen(d, p)

    # Dérivation déterministe de rho et sigma.
    digest = hashlib.sha3_512(d + bytes([p.k])).digest()
    rho = digest[:32]
    sigma = digest[32:]

    expected_rho = (
        "344badd000f8d8c537c48f998f05307c"
        "ebd1ede0b81c3bc59a065a1b6d63b26c"
    )

    expected_sigma = (
        "4e79e79f91f0b030bb5c3cd4668d21a1"
        "61dc5f139261c0c2f9213b29e5a0ce99"
    )

    expected_t_hat_sha256 = (
        "779d3291ad02f336c1c1722816e9631b"
        "d14c2a338db83d62cbd1684509707231"
    )

    assert rho.hex() == expected_rho
    assert sigma.hex() == expected_sigma

    # La clé publique contient t_hat encodé, puis rho.
    encoded_t_hat = ek[:p.dk_pke_size]

    assert hashlib.sha256(encoded_t_hat).hexdigest() == (
        expected_t_hat_sha256
    )
    assert ek[-32:] == rho