import sys, pathlib, random
from statistics import mean
from time import perf_counter_ns

M3 = pathlib.Path(__file__).resolve().parent.parent.parent / "m3-code"
if not M3.exists():
    sys.exit(f"Dossier {M3} introuvable (git worktree add ..\\m3-code origin/membre3)")
sys.path.insert(1, str(M3))

import mlkem
from params import ML_KEM_768 as P
from kyberslash_demo import welch_t_statistic

N = 150  # mesures par classe ; baisse la valeur si c'est trop lent

ek, dk = mlkem.keygen(P)
K, c = mlkem.encaps(ek, P)

def tamper(c):
    i = random.randrange(len(c))
    b = bytearray(c)
    b[i] ^= 1 << random.randrange(8)
    return bytes(b)

# Controle fonctionnel : valide -> meme cle, modifie -> cle differente, sans erreur
assert mlkem.decaps(dk, c, P) == K, "decaps valide : mauvaise cle"
assert mlkem.decaps(dk, tamper(c), P) != K, "rejet implicite : cle inchangee"
print("Controle OK : valide -> bonne cle, modifie -> cle de rejet.")

cases = [0] * N + [1] * N
random.shuffle(cases)
t = ([], [])
for g in cases:
    cc = c if g == 0 else tamper(c)
    s = perf_counter_ns()
    mlkem.decaps(dk, cc, P)
    t[g].append(perf_counter_ns() - s)

print(f"valide  : {mean(t[0])/1e6:.2f} ms")
print(f"modifie : {mean(t[1])/1e6:.2f} ms")
print(f"t de Welch = {welch_t_statistic(*t):+.2f}  (seuil dudect : 4.5)")