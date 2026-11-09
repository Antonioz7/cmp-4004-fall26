"""Provided tests for the week-10 TSP studio.

Run: ``python3 test_localsearch.py``. Prints one line per test. Passing means
your two genetic operators are correct AND you have confronted the honest result
the lesson insists on -- INCLUDING the test that refuses to let the GA look good
for free:

``test_honest_2opt_not_beaten_by_naive_ga`` asserts that, at an EQUAL evaluation
budget on the provided 30-city instance, a 2-opt hill climber is *not* beaten by
a naive GA (it wins on average across seeds). Every year someone reports this as
a bug -- "shouldn't the genetic algorithm win?". It is not a bug. A GA is a
design space, not a magic wand; on TSP with a proper 2-opt neighbourhood, simple
local search frequently wins at equal budget. Reporting that is the lesson.
"""
import random
import sys

import numpy as np

from localsearch import (
    load_tsp, validate_tour, one_point_crossover,
    tsp_hill_climb, tsp_genetic_algorithm,
)
import starter as s

TSP = load_tsp()
N = TSP.n
SEEDS = range(6)          # fixed -> the whole suite is deterministic


def test_swap_mutation_valid_permutation():
    """A swap can never create a duplicate: every mutant must be a valid tour of
    the same length."""
    for i in range(200):
        rng = random.Random(i)
        tour = TSP.random_tour(rng)
        mut = s.swap_mutation(tour, rng)
        assert validate_tour(mut, N), f"swap_mutation produced an invalid tour: {mut}"
        assert len(mut) == N
    print(f"  ok  swap_mutation always returns a valid {N}-city tour (200 trials)")


def test_order_crossover_produces_valid_tours():
    """THE Task-1 lesson. Order crossover must yield a valid permutation for
    every parent pair -- this is precisely what plain one-point crossover fails
    to do (see the contrast test below)."""
    for i in range(300):
        rng = random.Random(i)
        p1, p2 = TSP.random_tour(rng), TSP.random_tour(rng)
        child = s.order_crossover(p1, p2, rng)
        assert validate_tour(child, N), (
            f"order_crossover produced an INVALID tour (repeat/missing city): {child}"
        )
    print("  ok  order_crossover produces valid tours on 300 parent pairs")


def test_one_point_crossover_is_invalid():
    """The trap, made concrete. One-point crossover splices two permutations and
    (almost always) produces repeated/missing cities. This is why permutation
    problems need OX -- watch the naive operator fail."""
    invalid = 0
    for i in range(200):
        rng = random.Random(1000 + i)
        p1, p2 = TSP.random_tour(rng), TSP.random_tour(rng)
        child = one_point_crossover(p1, p2, rng)
        if not validate_tour(child, N):
            invalid += 1
    assert invalid > 0, (
        "one_point_crossover returned a VALID tour every time -- it should break "
        "the permutation on this instance. That it breaks is the point."
    )
    print(f"  ok  one_point_crossover breaks validity on {invalid}/200 pairs "
          "(and that is why you write OX)")


def test_ga_beats_random_baseline():
    """Sanity: with working operators, the GA must at least beat random search
    by a wide margin at 20k evaluations."""
    rng = random.Random(42)
    random_mean = np.mean([TSP.length(TSP.random_tour(rng)) for _ in range(100)])
    ga_len, _ = tsp_genetic_algorithm(
        TSP, s.order_crossover, s.swap_mutation, random.Random(0), max_evals=20_000)
    assert ga_len < 0.6 * random_mean, (
        f"GA tour {ga_len:.1f} is not much better than random mean {random_mean:.1f}"
    )
    print(f"  ok  GA ({ga_len:.1f}) beats random baseline ({random_mean:.1f})")


def test_honest_2opt_not_beaten_by_naive_ga():
    """The honest result (plan §10B): at EQUAL evaluation budget, 2-opt hill
    climbing is not beaten by a naive GA on this TSP -- it wins on average across
    seeds. The tidy 'evolution wins' story does NOT hold here, by design."""
    ga_lens, hc_lens = [], []
    for seed in SEEDS:
        ga, _ = tsp_genetic_algorithm(
            TSP, s.order_crossover, s.swap_mutation, random.Random(seed),
            max_evals=20_000)
        _, hc = tsp_hill_climb(TSP, random.Random(seed), max_evals=20_000)
        ga_lens.append(ga)
        hc_lens.append(hc)
    ga_mean, hc_mean = np.mean(ga_lens), np.mean(hc_lens)
    wins = sum(h <= g for h, g in zip(hc_lens, ga_lens))
    assert hc_mean < ga_mean, (
        f"expected 2-opt hill climbing to beat the naive GA at equal budget, but "
        f"HC mean {hc_mean:.1f} >= GA mean {ga_mean:.1f}. If your GA suddenly wins, "
        "check you are comparing at equal EVALUATIONS, not equal generations."
    )
    print(f"  ok  2-opt hill climbing beats naive GA at equal budget "
          f"(HC {hc_mean:.1f} < GA {ga_mean:.1f}; HC wins {wins}/{len(hc_lens)} seeds -- the lesson)")


TESTS = [
    test_swap_mutation_valid_permutation,
    test_order_crossover_produces_valid_tours,
    test_one_point_crossover_is_invalid,
    test_ga_beats_random_baseline,
    test_honest_2opt_not_beaten_by_naive_ga,
]


def main():
    failed = 0
    for t in TESTS:
        try:
            t()
        except NotImplementedError:
            print(f"  --  {t.__name__}: operator not implemented yet")
            failed += 1
        except AssertionError as e:
            print(f"  FAIL {t.__name__}: {e}")
            failed += 1
    if failed:
        print(f"\n{failed}/{len(TESTS)} failed")
        sys.exit(1)
    print(f"\nall {len(TESTS)} tests pass")


if __name__ == "__main__":
    main()
