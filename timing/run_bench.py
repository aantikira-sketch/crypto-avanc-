import ctypes, csv, pathlib, random
from statistics import mean
from kyberslash_demo import welch_t_statistic

Q, N, BATCHES = 3329, 2000, 2000
here = pathlib.Path(__file__).parent
lib = ctypes.CDLL(str(here / "bench.dll"))
lib.bench.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_uint32), ctypes.c_int]
lib.bench.restype = ctypes.c_double

NAMES = ["msg_div", "msg_fix", "comp4_div", "comp4_fix"]
fixed = (ctypes.c_uint32 * N)(*([1000] * N))

def rand_arr():
    return (ctypes.c_uint32 * N)(*random.choices(range(Q), k=N))

data = {}
with open(here / "results.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["function", "class", "ns_per_call"])
    for idx, name in enumerate(NAMES):
        for _ in range(50):                      # échauffement
            lib.bench(idx, fixed, N)
        order = ["fixed"] * BATCHES + ["random"] * BATCHES
        random.shuffle(order)                    # ordre mélangé
        t = {"fixed": [], "random": []}
        for cls in order:
            arr = fixed if cls == "fixed" else rand_arr()
            v = lib.bench(idx, arr, N)
            t[cls].append(v)
            w.writerow([name, cls, f"{v:.4f}"])
        data[name] = t
        tv = welch_t_statistic(t["fixed"], t["random"])
        print(f"{name:10s} fixe={mean(t['fixed']):.3f} ns  "
              f"alea={mean(t['random']):.3f} ns  t={tv:+.2f}")

print("Seuil dudect : |t| > 4.5 => fuite probable. Brut dans timing/results.csv")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(2, 2, figsize=(10, 7))
    for ax, name in zip(axs.flat, NAMES):
        for cls in ("fixed", "random"):
            ax.hist(data[name][cls], bins=60, alpha=0.5, label=cls)
        ax.set_title(name); ax.set_xlabel("ns / appel"); ax.legend()
    plt.tight_layout()
    plt.savefig(here / "hist.png", dpi=150)
    print("Graphique : timing/hist.png")
except ImportError:
    print("matplotlib absent : pip install matplotlib puis relance")