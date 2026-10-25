import hashlib

def _shake(data, n): return hashlib.shake_256(data).digest(n)
def _xor(a, b): return bytes(x ^ y for x, y in zip(a, b))

def k_pke_keygen(d, p):
    dk = _shake(b"dk" + d, p.dk_pke_size)
    ek = dk + _shake(b"rho" + d, 32)
    return ek, dk

def k_pke_encrypt(ek, m, r, p):
    key = ek[:p.dk_pke_size]
    return _xor(m, _shake(key, 32)) + _shake(m + r, p.c_size - 32)

def k_pke_decrypt(dk, c, p):
    return _xor(c[:32], _shake(dk, 32))