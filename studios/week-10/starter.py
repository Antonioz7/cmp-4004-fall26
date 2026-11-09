"""Week 10 studio — starter (genetic operators for TSP + the study harness).

You fill in TWO operators. Run ``python3 test_localsearch.py`` as you go.

  Task 1  order_crossover / swap_mutation  -- the two TSP genetic operators.
  Task 2  run_study()                       -- the hyperparameter study harness.

THE TRAP (plan §10B, Task 1): standard one-point crossover splices two tours and
produces REPEATED / MISSING cities -- an invalid tour. ``localsearch`` ships the
broken ``one_point_crossover`` and a ``validate_tour`` checker so you can watch it
fail, then fix it with **order crossover (OX)**. Write ``order_crossover`` so that
every child is a valid permutation.

THE HONEST RESULT (plan §10B): at an equal EVALUATION budget, a 2-opt hill
climber often BEATS a naive GA on TSP. ``test_localsearch.py`` asserts exactly
that on the provided instance. A GA is not automatically better for being
biologically inspired -- report what you measure.
"""
import random

from localsearch import (
    TSP, load_tsp, load_instances, validate_tour,
    one_point_crossover, two_opt_neighbors,
    tsp_hill_climb, tsp_genetic_algorithm,
)


# ---- Task 1: the two TSP genetic operators ----------------------------------

def order_crossover(parent1, parent2, rng):
    """Order crossover (OX). Returns a child that is a VALID permutation.

    Recipe:
      1. Pick two cut points a <= b (e.g. ``sorted(rng.sample(range(n), 2))``).
      2. Copy parent1[a..b] straight into the child at the same positions.
      3. Fill the remaining positions -- walking from b+1, wrapping around --
         with the cities of parent2 IN parent2's order, skipping any already
         copied from parent1.
    The segment-copy + ordered-fill is what guarantees no city repeats or goes
    missing, which plain one-point crossover cannot promise.
    """
    # TODO: implement OX so that validate_tour(child, len(parent1)) is True.
    raise NotImplementedError


def swap_mutation(tour, rng):
    """Swap mutation: return a NEW tour with two positions exchanged. Always a
    valid permutation (a swap cannot create duplicates)."""
    # TODO: copy the tour, pick two indices, swap them, return the new tour.
    raise NotImplementedError


# ---- Task 2: the hyperparameter study (fill in after Task 1 passes) ---------

def run_study(tsp=None, n_seeds=5, max_evals=20_000):
    """The real study (plan §10B, Task 2). Vary population (20, 50, 100) x
    mutation rate (0.001, 0.01, 0.1) x tournament (2, 5), FIVE SEEDS each, at a
    FIXED EVALUATION BUDGET (not fixed generations -- that silently favours large
    populations). Return rows of (pop, mut, tourn, mean_len, std_len).

    Also run the CROSSOVER ABLATION: the same grid with use_crossover=False, and
    ask whether crossover helps on THIS problem. Answer with data.

    Deliverables (see README): mean +/- std table, a population x mutation
    heatmap, one convergence plot with error bands, and the ablation.
    """
    import numpy as np
    tsp = tsp or load_tsp()
    rows = []
    for pop in (20, 50, 100):
        for mut in (0.001, 0.01, 0.1):
            for tourn in (2, 5):
                # TODO: run tsp_genetic_algorithm for n_seeds seeds with these
                # params (rng=random.Random(SEED_BASE + s)), collect best_len,
                # and append (pop, mut, tourn, mean, std). Use np.mean / np.std.
                raise NotImplementedError
    return rows


if __name__ == "__main__":
    # Smoke test: run each method once on the provided instance.
    tsp = load_tsp()
    rng = random.Random(20250806)
    nn = tsp.nearest_neighbor_tour()
    print(f"instance: {tsp.n} cities")
    print(f"  random tour        len = {tsp.length(tsp.random_tour(rng)):.1f}")
    print(f"  nearest-neighbour  len = {tsp.length(nn):.1f}")
    hc_tour, hc_len = tsp_hill_climb(tsp, random.Random(1), max_evals=20_000)
    print(f"  2-opt hill climb   len = {hc_len:.1f}")
    try:
        ga_len, _ = tsp_genetic_algorithm(
            tsp, order_crossover, swap_mutation, random.Random(1), max_evals=20_000)
        print(f"  naive GA           len = {ga_len:.1f}")
    except NotImplementedError:
        print("  naive GA           -- operators not implemented yet")
