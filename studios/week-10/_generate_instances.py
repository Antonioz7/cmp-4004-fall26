"""Instance generator for the week-10 TSP studio. Run once at build time; it
commits ``instances.json`` alongside. Deterministic (SEED = 20250806, the same
seed the Session-A notebook uses).

WHY THIS FILE EXISTS (honest note): the lesson plan promises a "30-city TSP
instance provided with a known-good tour", but the Session-A notebook only ever
builds an 8-queens and a knapsack instance — there is no TSP anywhere in it. So
the 30-city instance could not be *copied* from the notebook; it is generated
here reproducibly from the notebook's seed rather than typed in by hand. Rotate
SEED and re-run to get a different instance.

Cities are uniform-random points in a 100 x 100 square. The stored
"nearest_neighbor_tour" is the greedy known-good baseline students compare
against (plan Session B, Task 1).
"""
import json
import random
from pathlib import Path

from localsearch import TSP

SEED = 20250806
N_CITIES = 30
FIELD = 100.0


def main():
    rng = random.Random(SEED)
    cities = [[round(rng.uniform(0, FIELD), 2), round(rng.uniform(0, FIELD), 2)]
              for _ in range(N_CITIES)]
    tsp = TSP(cities)
    nn_tour = tsp.nearest_neighbor_tour(start=0)
    out = {
        "seed": SEED,
        "n_cities": N_CITIES,
        "field": FIELD,
        "cities": cities,
        "nearest_neighbor_tour": nn_tour,
        "nearest_neighbor_length": round(tsp.length(nn_tour), 4),
    }
    dest = Path(__file__).with_name("instances.json")
    dest.write_text(json.dumps(out, indent=2))
    print(f"wrote {dest} — {N_CITIES} cities, "
          f"NN tour length {out['nearest_neighbor_length']}")


if __name__ == "__main__":
    main()
