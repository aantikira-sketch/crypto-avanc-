import hashlib, os
from hmac import compare_digest
import kpke          # plus tard : import kpke

def G(x): return hashlib.sha3_512(x).digest()        # 64 octets
def H(x): return hashlib.sha3_256(x).digest()        # 32 octets
def J(x): return hashlib.shake_256(x).digest(32)     # 32 octets

def keygen_internal(d, z, p):
    ek, dk_pke = kpke.k_pke_keygen(d, p)
    dk = dk_pke + ek + H(ek) + z
    return ek, dk

def keygen(p):
    return keygen_internal(os.urandom(32), os.urandom(32), p)

def encaps_internal(ek, m, p):
    kr = G(m + H(ek))
    K, r = kr[:32], kr[32:]
    return K, kpke.k_pke_encrypt(ek, m, r, p)

def encaps(ek, p):
    return encaps_internal(ek, os.urandom(32), p)

def _select(ok, a, b):
    """Renvoie a si ok vaut 1, sinon b, sans if sur la valeur secrète."""
    mask = -ok & 0xFF
    return bytes((x & mask) | (y & ~mask & 0xFF) for x, y in zip(a, b))

def decaps(dk, c, p):
    k = p.k
    dk_pke = dk[0 : 384*k]
    ek_pke = dk[384*k : 768*k + 32]
    h      = dk[768*k + 32 : 768*k + 64]
    z      = dk[768*k + 64 : 768*k + 96]

    m2 = kpke.k_pke_decrypt(dk_pke, c, p)      # 1. déchiffrer
    kr = G(m2 + h)                             # 2. recalculer K' et r'
    K2, r2 = kr[:32], kr[32:]
    K_rejet = J(z + c)                         # 3. fausse clé de secours
    c2 = kpke.k_pke_encrypt(ek_pke, m2, r2, p) # 4. re-chiffrer
    ok = int(compare_digest(c, c2))            # 5. comparer
    return _select(ok, K2, K_rejet)            # 6. bonne clé ou fausse clé
