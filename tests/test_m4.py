import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "timing"))
from kyberslash_demo import Q, vulnerable_compress, corrected_compress
from ct_demo import cmp_early, cmp_ct, select_ct


def test_compress_equivalence():
    assert all(vulnerable_compress(x) == corrected_compress(x) for x in range(Q))


def test_cmp_ct_matches_early():
    a = bytes(range(32))
    b = bytearray(a); b[5] ^= 1
    assert cmp_ct(a, a) and cmp_early(a, a)
    assert not cmp_ct(a, bytes(b)) and not cmp_early(a, bytes(b))


def test_select_ct():
    k, kr = b"\x01" * 32, b"\x02" * 32
    assert select_ct(True, k, kr) == k
    assert select_ct(False, k, kr) == kr
    