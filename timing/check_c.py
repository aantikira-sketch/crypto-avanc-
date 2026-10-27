import ctypes, pathlib
lib = ctypes.CDLL(str(pathlib.Path(__file__).with_name("kyberslash.dll")))
for name in ("msg_div", "msg_fix", "comp4_div", "comp4_fix"):
    f = getattr(lib, name)
    f.argtypes = [ctypes.c_uint32]
    f.restype = ctypes.c_uint32

Q = 3329
for x in range(Q):
    assert lib.msg_div(x) == lib.msg_fix(x), f"msg x={x}"
    assert lib.comp4_div(x) == lib.comp4_fix(x), f"comp4 x={x}"
print("OK : equivalence C verifiee pour x = 0..3328")