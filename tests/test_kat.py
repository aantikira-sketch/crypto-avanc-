import json, pathlib
import pytest
from params import ML_KEM_512, ML_KEM_768, ML_KEM_1024
import mlkem

KAT_DIR = pathlib.Path(__file__).parent / "kat"
PARAMS = {p.name: p for p in (ML_KEM_512, ML_KEM_768, ML_KEM_1024)}
h = bytes.fromhex

pytestmark = pytest.mark.skipif(
    mlkem.kpke.__name__ == "fake_kpke",
    reason="Le vrai K-PKE n'est pas encore branché",
)

def _groups(name, function=None):
    data = json.loads((KAT_DIR / name).read_text(encoding="utf-8"))
    for g in data["testGroups"]:
        if function is None or g.get("function") == function:
            yield g, PARAMS[g["parameterSet"]]

def test_keygen_kat():
    n = 0
    for g, p in _groups("keygen.json"):
        for t in g["tests"]:
            ek, dk = mlkem.keygen_internal(h(t["d"]), h(t["z"]), p)
            assert ek == h(t["ek"]), f"ek faux ({p.name}, tcId {t['tcId']})"
            assert dk == h(t["dk"]), f"dk faux ({p.name}, tcId {t['tcId']})"
            n += 1
    assert n > 0

def test_encaps_kat():
    n = 0
    for g, p in _groups("encapdecap.json", "encapsulation"):
        for t in g["tests"]:
            K, c = mlkem.encaps_internal(h(t["ek"]), h(t["m"]), p)
            assert c == h(t["c"]), f"c faux ({p.name}, tcId {t['tcId']})"
            assert K == h(t["k"]), f"K faux ({p.name}, tcId {t['tcId']})"
            n += 1
    assert n > 0

def test_decaps_kat():
    n = 0
    for g, p in _groups("encapdecap.json", "decapsulation"):
        for t in g["tests"]:
            K = mlkem.decaps_internal(h(t["dk"]), h(t["c"]), p)
            assert K == h(t["k"]), f"K faux ({p.name}, tcId {t['tcId']}, {t['reason']})"
            n += 1
    assert n > 0