import json, pathlib
from params import ML_KEM_512, ML_KEM_768, ML_KEM_1024
import mlkem

KAT_DIR = pathlib.Path(__file__).parent / "kat"
PARAMS = {p.name: p for p in (ML_KEM_512, ML_KEM_768, ML_KEM_1024)}
h = bytes.fromhex

def _groups(name):
    data = json.loads((KAT_DIR / name).read_text(encoding="utf-8"))
    return data["testGroups"]

def test_keygen_structure_dk():
    n = 0
    for g in _groups("keygen.json"):
        p = PARAMS[g["parameterSet"]]
        k = p.k
        for t in g["tests"]:
            ek, dk, z = h(t["ek"]), h(t["dk"]), h(t["z"])
            assert len(ek) == p.ek_size and len(dk) == p.dk_size
            assert dk[384*k : 768*k + 32] == ek
            assert dk[768*k + 32 : 768*k + 64] == mlkem.H(ek)
            assert dk[768*k + 64 :] == z
            n += 1
    assert n > 0

def test_encaps_cle_K():
    n = 0
    for g in _groups("encapdecap.json"):
        if g.get("function") != "encapsulation":
            continue
        p = PARAMS[g["parameterSet"]]
        for t in g["tests"]:
            K = mlkem.G(h(t["m"]) + mlkem.H(h(t["ek"])))[:32]
            assert K == h(t["k"]), f"K faux (tcId {t['tcId']})"
            assert len(h(t["c"])) == p.c_size
            n += 1
    assert n > 0