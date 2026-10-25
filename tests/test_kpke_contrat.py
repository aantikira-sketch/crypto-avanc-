import importlib
import pytest
from params import ML_KEM_512, ML_KEM_768, ML_KEM_1024

ALL = [ML_KEM_512, ML_KEM_768, ML_KEM_1024]

def _charge(nom):
    mod = importlib.import_module(nom)
    for f in ("k_pke_keygen", "k_pke_encrypt", "k_pke_decrypt"):
        if not hasattr(mod, f):
            pytest.skip(f"{nom}.{f} pas encore écrit")
    return mod

@pytest.fixture(params=["fake_kpke", "kpke"])
def K(request):
    return _charge(request.param)

@pytest.mark.parametrize("p", ALL)
def test_tailles(K, p):
    d, m, r = bytes(range(32)), bytes(range(32, 64)), bytes(range(64, 96))
    ek, dk = K.k_pke_keygen(d, p)
    c = K.k_pke_encrypt(ek, m, r, p)
    assert len(ek) == p.ek_size
    assert len(dk) == p.dk_pke_size
    assert len(c) == p.c_size
    assert len(K.k_pke_decrypt(dk, c, p)) == 32

@pytest.mark.parametrize("p", ALL)
def test_aller_retour(K, p):
    for i in range(20):
        d = bytes([i]) * 32
        m = bytes([255 - i]) * 32
        r = bytes([(7 * i) % 256]) * 32
        ek, dk = K.k_pke_keygen(d, p)
        c = K.k_pke_encrypt(ek, m, r, p)
        assert K.k_pke_decrypt(dk, c, p) == m

@pytest.mark.parametrize("p", ALL)
def test_deterministe(K, p):
    d, m, r = b"\x01" * 32, b"\x02" * 32, b"\x03" * 32
    assert K.k_pke_keygen(d, p) == K.k_pke_keygen(d, p)
    ek, _ = K.k_pke_keygen(d, p)
    assert K.k_pke_encrypt(ek, m, r, p) == K.k_pke_encrypt(ek, m, r, p)

@pytest.mark.parametrize("p", ALL)
def test_r_change_le_chiffre(K, p):
    d, m = b"\x01" * 32, b"\x02" * 32
    ek, _ = K.k_pke_keygen(d, p)
    assert K.k_pke_encrypt(ek, m, b"\x03" * 32, p) != K.k_pke_encrypt(ek, m, b"\x04" * 32, p)