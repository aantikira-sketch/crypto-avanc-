import pytest

import hashlib
from encoding import ByteDecode

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
    """Vérifie rho, sigma et t_hat avec une graine fixe."""
    d = bytes(range(32))
    p = ML_KEM_512

    ek, _ = k_pke_keygen(d, p)

    # Vérification de rho et sigma
    digest = hashlib.sha3_512(d + bytes([p.k])).digest()
    rho = digest[:32]
    sigma = digest[32:]

    assert ek[-32:] == rho
    assert len(sigma) == 32

    # Vérification de t_hat, encodé dans la clé publique
    encoded_t_hat = ek[:p.dk_pke_size]
    t_hat = ByteDecode(12, encoded_t_hat[:384])

    assert len(t_hat) == 256
    assert all(0 <= coefficient < 4096 for coefficient in t_hat)