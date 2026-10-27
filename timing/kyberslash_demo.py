
# Prototype M4 : equivalence et mesures temporelles
from time import perf_counter_ns
from statistics import mean
import random

Q = 3329
SAMPLES = 2_000


def vulnerable_compress(x: int) -> int:
    """Version de reference avec division."""
    return (x * 256 + Q // 2) // Q


def corrected_compress(x: int) -> int:
    """Version corrigee par multiplication et decalage."""
    numerator = x * 256 + Q // 2
    multiplier = (1 << 32) // Q + 1
    return (numerator * multiplier) >> 32


def check_equivalence() -> None:
    for x in range(Q):
        assert vulnerable_compress(x) == corrected_compress(x), (
            f"Difference pour x={x}"
        )
    print(f"Equivalence verifiee pour les {Q} valeurs.")


def measure(func, values):
    durations = []
    for x in values:
        start = perf_counter_ns()
        func(x)
        durations.append(perf_counter_ns() - start)
    return durations


def welch_t_statistic(a, b):
    """Statistique t de Welch avec calculs efficaces."""
    mean_a = mean(a)
    mean_b = mean(b)

    variance_a = sum((x - mean_a) ** 2 for x in a) / (len(a) - 1)
    variance_b = sum((x - mean_b) ** 2 for x in b) / (len(b) - 1)

    denominator = (variance_a / len(a) + variance_b / len(b)) ** 0.5

    if denominator == 0:
        return 0.0

    return (mean_a - mean_b) / denominator


def timing_experiment(func, label):
    # Deux classes d'entrees : valeurs fixes et valeurs aleatoires
    fixed_values = [1000] * SAMPLES
    random_values = [random.randrange(Q) for _ in range(SAMPLES)]

    # Melanger l'ordre pour limiter certains biais de mesure
    cases = [(0, x) for x in fixed_values] + [(1, x) for x in random_values]
    random.shuffle(cases)

    fixed_times = []
    random_times = []

    for group, x in cases:
        start = perf_counter_ns()
        func(x)
        elapsed = perf_counter_ns() - start

        if group == 0:
            fixed_times.append(elapsed)
        else:
            random_times.append(elapsed)

    t = welch_t_statistic(fixed_times, random_times)
    print(f"\n{label}")
    print(f"Moyenne classe fixe    : {mean(fixed_times):.1f} ns")
    print(f"Moyenne classe aleatoire: {mean(random_times):.1f} ns")
    print(f"Statistique t de Welch : {t:.3f}")


if __name__ == "__main__":
    check_equivalence()
    timing_experiment(vulnerable_compress, "Version avec division")
    timing_experiment(corrected_compress, "Version multipliee-decalee")
