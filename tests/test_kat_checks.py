import json, pathlib
from params import ML_KEM_512, ML_KEM_768, ML_KEM_1024
import mlkem

KAT_DIR = pathlib.Path(__file__).parent / "kat"
PARAMS = {p.name: p for p in (ML_KEM_512, ML_KEM_768, ML_KEM_1024)}
h = bytes.fromhex

def _groups(function):
    data = json.loads((KAT_DIR / "encapdecap.json").read_text(encoding="utf-8"))
    return [g for g in data["testGroups"] if g.get("function") == function]

def _passe(check, *args):
    try:
        check(*args)
        return True
    except ValueError:
        return False

def _verifie(function, check, champ, monkeypatch):
    monkeypatch.setattr(mlkem, "CHECK_EK_MODULUS", True)
    attendus = set()
    for g in _groups(function):
        p = PARAMS[g["parameterSet"]]
        for t in g["tests"]:
            got = _passe(check, h(t[champ]), p)
            assert got == t["testPassed"], (
                f"{p.name} tcId {t['tcId']} : obtenu {got}, "
                f"attendu {t['testPassed']} ({t['reason']})")
            attendus.add(t["testPassed"])
    assert attendus == {True, False}   # le test n'est pas vide de sens

def test_encaps_key_check(monkeypatch):
    _verifie("encapsulationKeyCheck", mlkem._check_ek, "ek", monkeypatch)

def test_decaps_key_check(monkeypatch):
    _verifie("decapsulationKeyCheck", mlkem._check_dk, "dk", monkeypatch)