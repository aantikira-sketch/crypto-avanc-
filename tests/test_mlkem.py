import pytest
from params import ML_KEM_512, ML_KEM_768, ML_KEM_1024
import mlkem

ALL = [ML_KEM_512, ML_KEM_768, ML_KEM_1024]

@pytest.mark.parametrize("p", ALL)
def test_tailles(p):
    ek, dk = mlkem.keygen(p)
    K, c = mlkem.encaps(ek, p)
    assert len(ek) == p.ek_size and len(dk) == p.dk_size
    assert len(c) == p.c_size and len(K) == 32

@pytest.mark.parametrize("p", ALL)
def test_aller_retour(p):
    for _ in range(50):
        ek, dk = mlkem.keygen(p)
        K, c = mlkem.encaps(ek, p)
        assert mlkem.decaps(dk, c, p) == K

@pytest.mark.parametrize("p", ALL)
def test_rejet_implicite(p):
    ek, dk = mlkem.keygen(p)
    K, c = mlkem.encaps(ek, p)
    bad = bytes([c[0] ^ 1]) + c[1:]
    K2 = mlkem.decaps(dk, bad, p)        # ne doit lever aucune exception
    assert K2 != K and len(K2) == 32
    assert mlkem.decaps(dk, bad, p) == K2  # toujours la même fausse clé

def test_encaps_aleatoire():
    ek, _ = mlkem.keygen(ML_KEM_768)
    assert mlkem.encaps(ek, ML_KEM_768)[1] != mlkem.encaps(ek, ML_KEM_768)[1]