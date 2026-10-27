import random
from time import perf_counter_ns
from kyberslash_demo import welch_t_statistic

L = 1088  # taille d'un chiffré ML-KEM-768


def cmp_early(a, b):
    """Comparaison qui s'arrête au premier octet différent (fuite)."""
    for x, y in zip(a, b):
        if x != y:
            return False
    return True


def cmp_ct(a, b):
    """Comparaison qui parcourt tout, sans branchement sur les données."""
    diff = 0
    for x, y in zip(a, b):
        diff |= x ^ y
    return diff == 0


def select_ct(equal, k, k_reject):
    """Renvoie k si equal, sinon k_reject, sans if."""
    mask = -int(equal) & 0xFF  # 0xFF si equal, 0 sinon
    return bytes((x & mask) | (y & ~mask & 0xFF) for x, y in zip(k, k_reject))


def experiment(func, label, n=3000):
    c = bytes(random.randrange(256) for _ in range(L))
    early = bytearray(c); early[0] ^= 1; early = bytes(early)
    late = bytearray(c); late[-1] ^= 1; late = bytes(late)
    cases = [0] * n + [1] * n
    random.shuffle(cases)
    t = ([], [])
    for g in cases:
        other = early if g == 0 else late
        s = perf_counter_ns()
        func(c, other)
        t[g].append(perf_counter_ns() - s)
    print(f"{label:10s} diff au 1er octet={sum(t[0])/n:.0f} ns  "
          f"au dernier={sum(t[1])/n:.0f} ns  t={welch_t_statistic(*t):+.1f}")


if __name__ == "__main__":
    experiment(cmp_early, "cmp_early")
    experiment(cmp_ct, "cmp_ct")