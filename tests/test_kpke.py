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
