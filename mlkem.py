import hashlib, os
from hmac import compare_digest
import kpke

Q = 3329
# Mettre True quand le vrai K-PKE est branché : le faux K-PKE
# produit des ek qui ne sont pas des coefficients valides modulo q.
CHECK_EK_MODULUS = True

def G(x): return hashlib.sha3_512(x).digest()
def H(x): return hashlib.sha3_256(x).digest()
def J(x): return hashlib.shake_256(x).digest(32)

# ---------- contrôles d'entrée (FIPS 203) ----------

def _check_ek(ek, p):
    if len(ek) != p.ek_size:
        raise ValueError("ek : mauvaise longueur")
    if CHECK_EK_MODULUS:
        t = ek[:384 * p.k]
        for i in range(0, len(t), 3):
            b0, b1, b2 = t[i], t[i + 1], t[i + 2]
            a0 = b0 | ((b1 & 0x0F) << 8)
            a1 = (b1 >> 4) | (b2 << 4)
            if a0 >= Q or a1 >= Q:
                raise ValueError("ek : coefficient >= q")

def _check_dk(dk, p):
    k = p.k
    if len(dk) != p.dk_size:
        raise ValueError("dk : mauvaise longueur")
    ek_pke = dk[384 * k : 768 * k + 32]
    h = dk[768 * k + 32 : 768 * k + 64]
    if not compare_digest(H(ek_pke), h):
        raise ValueError("dk : hash de ek incohérent")

def _check_c(c, p):
    if len(c) != p.c_size:
        raise ValueError("c : mauvaise longueur")

# ---------- KeyGen ----------

def keygen_internal(d, z, p):
    ek, dk_pke = kpke.k_pke_keygen(d, p)
    return ek, dk_pke + ek + H(ek) + z

def keygen(p):
    return keygen_internal(os.urandom(32), os.urandom(32), p)

# ---------- Encaps ----------

def encaps_internal(ek, m, p):
    kr = G(m + H(ek))
    K, r = kr[:32], kr[32:]
    return K, kpke.k_pke_encrypt(ek, m, r, p)

def encaps(ek, p):
    _check_ek(ek, p)
    return encaps_internal(ek, os.urandom(32), p)

# ---------- Decaps ----------

def _select(ok, a, b):
    """Renvoie a si ok vaut 1, sinon b, sans if sur la valeur secrète."""
    mask = -ok & 0xFF
    return bytes((x & mask) | (y & ~mask & 0xFF) for x, y in zip(a, b))

def decaps_internal(dk, c, p):
    k = p.k
    dk_pke = dk[0 : 384 * k]
    ek_pke = dk[384 * k : 768 * k + 32]
    h      = dk[768 * k + 32 : 768 * k + 64]
    z      = dk[768 * k + 64 : 768 * k + 96]

    m2 = kpke.k_pke_decrypt(dk_pke, c, p)
    kr = G(m2 + h)
    K2, r2 = kr[:32], kr[32:]
    K_rejet = J(z + c)
    c2 = kpke.k_pke_encrypt(ek_pke, m2, r2, p)
    ok = int(compare_digest(c, c2))
    return _select(ok, K2, K_rejet)

def decaps(dk, c, p):
    _check_c(c, p)
    _check_dk(dk, p)
    return decaps_internal(dk, c, p)
