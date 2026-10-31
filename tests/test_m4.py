import ctypes, pathlib, sys
import pytest

TIMING = pathlib.Path(__file__).parent.parent / "timing"
sys.path.insert(0, str(TIMING))
from kyberslash_demo import Q, vulnerable_compress, corrected_compress
from ct_demo import cmp_early, cmp_ct, select_ct

DLL = TIMING / "kyberslash.dll"


def test_compress_equivalence():
    assert all(vulnerable_compress(x) == corrected_compress(x) for x in range(Q))


@pytest.mark.skipif(not DLL.exists(), reason="kyberslash.dll non compilee")
def test_c_equivalence():
    lib = ctypes.CDLL(str(DLL))
    for name in ("msg_div", "msg_fix", "comp4_div", "comp4_fix"):
        f = getattr(lib, name)
        f.argtypes = [ctypes.c_uint32]
        f.restype = ctypes.c_uint32
    for x in range(Q):
        assert lib.msg_div(x) == lib.msg_fix(x), f"msg x={x}"
        assert lib.comp4_div(x) == lib.comp4_fix(x), f"comp4 x={x}"


def test_cmp_all_positions():
    a = bytes(range(32))
    assert cmp_ct(a, a) and cmp_early(a, a)
    for i in range(32):
        for bit in range(8):
            b = bytearray(a)
            b[i] ^= 1 << bit
            assert not cmp_ct(a, bytes(b)), f"cmp_ct pos={i}"
            assert not cmp_early(a, bytes(b)), f"cmp_early pos={i}"


def test_cmp_different_lengths():
    a = bytes(range(32))
    for other in (a + b"\x00", a[:-1], b""):
        assert not cmp_ct(a, other)
        assert not cmp_ct(other, a)
        assert not cmp_early(a, other)
        assert not cmp_early(other, a)


def test_select_ct():
    k, kr = b"\x01" * 32, b"\x02" * 32
    assert select_ct(True, k, kr) == k
    assert select_ct(False, k, kr) == kr