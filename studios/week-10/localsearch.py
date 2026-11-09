"""Week 10 studio — the shared local-search engine (GIVEN; do not modify).

Session B is a *studio on the travelling-salesperson problem* (TSP). This file
provides everything you are NOT asked to write:

  * generic ``hill_climb`` and ``simulated_annealing`` (the plan's forms)
  * a ``TSP`` problem: tour length, validity check, random & nearest-neighbour
    tours, and a 2-opt neighbourhood
  * budget-aware drivers ``tsp_hill_climb`` and ``tsp_genetic_algorithm`` that
    compare methods at an EQUAL EVALUATION BUDGET (not equal generations)
  * a deliberately BROKEN ``one_point_crossover`` — the trap the plan wants you
    to hit, so ``validate_tour`` can catch it immediately
  * the Session-A knapsack code, extracted VERBATIM from the notebook, as a
    reference second problem (not used by the studio tests)

You implement the two TSP genetic operators in ``starter.py``:
``order_crossover`` (OX) and ``swap_mutation``. The engine's GA calls into them.

Interface used by the studio:
    TSP(cities).length(tour)          -> float total Euclidean tour length
    TSP(cities).valid_tour(tour)      -> bool (a permutation of 0..n-1)
    TSP(cities).random_tour(rng)      -> a random valid tour
    TSP(cities).nearest_neighbor_tour(start=0) -> a greedy "known-good" tour
    two_opt_neighbors(tour)           -> generator of 2-opt neighbour tours
    tsp_hill_climb(tsp, rng, ...)     -> (best_tour, best_len)
    tsp_genetic_algorithm(tsp, crossover, mutation, rng, ...) -> (best_len, trace)
"""
import json
import math
import random
from pathlib import Path

SEED = 20250806          # the notebook's seed — reused so results are reproducible


# =============================================================================
# Generic local search (the forms from the lesson plan). A ``problem`` exposes
# ``value(state)`` (higher is better — we MAXIMISE) and ``neighbors(state)``.
# =============================================================================

def hill_climb(problem, state, allow_sideways=0):
    """Steepest-ascent hill climbing. Returns (state, reason, steps).

    ``allow_sideways`` caps equal-value moves so we can cross plateaus — the one
    small change that turned 8-queens from ~14% to ~94% success in the notebook.
    """
    sideways, steps = 0, 0
    while True:
        nbrs = list(problem.neighbors(state))
        best = max(nbrs, key=problem.value)
        if problem.value(best) > problem.value(state):
            state, sideways = best, 0
        elif problem.value(best) == problem.value(state) and sideways < allow_sideways:
            state, sideways = best, sideways + 1        # PLATEAU move
        else:
            return state, ("solved" if _at_optimum(problem, state) else "stuck"), steps
        steps += 1


def _at_optimum(problem, state):
    # A local peak by definition — no strictly-better neighbour exists.
    v = problem.value(state)
    return all(problem.value(nb) <= v for nb in problem.neighbors(state))


def exp_schedule(T0=2.0, decay=0.9995):
    """Exponential cooling schedule (verbatim from the notebook)."""
    return lambda t: T0 * (decay ** t)


def simulated_annealing(problem, state, schedule, rng, max_steps=60_000, record=False):
    """Accept a worse move with probability exp(ΔE / T). High T → random walk,
    low T → hill climbing. Generic form of the notebook's SA."""
    current = state
    trace = []
    for t in range(1, max_steps + 1):
        T = schedule(t)
        if T <= 1e-12:
            break
        candidate = rng.choice(list(problem.neighbors(current)))
        delta = problem.value(candidate) - problem.value(current)
        if delta > 0 or rng.random() < math.exp(delta / T):
            current = candidate
        if record:
            trace.append(problem.value(current))
    return current, trace


# =============================================================================
# The studio problem: TSP
# =============================================================================

class TSP:
    """Euclidean TSP. A *state* / *tour* is a permutation of city indices
    0..n-1; the salesperson returns to the start, so the last→first leg counts.
    ``value`` is the NEGATIVE tour length (we maximise value ⇔ minimise length)."""

    def __init__(self, cities):
        self.cities = [tuple(c) for c in cities]
        self.n = len(self.cities)

    def dist(self, a, b):
        (x1, y1), (x2, y2) = self.cities[a], self.cities[b]
        return math.hypot(x1 - x2, y1 - y2)

    def length(self, tour):
        return sum(self.dist(tour[i], tour[(i + 1) % self.n]) for i in range(self.n))

    def value(self, tour):
        return -self.length(tour)

    def valid_tour(self, tour):
        """A tour is valid iff it is a permutation of 0..n-1 (no repeats/omissions)."""
        return len(tour) == self.n and sorted(tour) == list(range(self.n))

    def random_tour(self, rng):
        t = list(range(self.n))
        rng.shuffle(t)
        return t

    def nearest_neighbor_tour(self, start=0):
        """Greedy 'known-good' baseline: always hop to the nearest unvisited city."""
        unvisited = set(range(self.n))
        tour = [start]
        unvisited.discard(start)
        while unvisited:
            last = tour[-1]
            nxt = min(unvisited, key=lambda c: self.dist(last, c))
            tour.append(nxt)
            unvisited.discard(nxt)
        return tour

    def neighbors(self, tour):
        """2-opt neighbourhood (so the generic ``hill_climb`` works on TSP too)."""
        return two_opt_neighbors(tour)


def two_opt_neighbors(tour):
    """Yield every 2-opt neighbour: reverse the segment tour[i..j]. Reversing a
    contiguous segment always yields another valid permutation — this is why
    2-opt is the natural neighbourhood for a permutation problem (and why plain
    one-point crossover, which does NOT preserve the permutation, is a trap)."""
    n = len(tour)
    for i in range(n - 1):
        for j in range(i + 1, n):
            nb = tour[:i] + tour[i:j + 1][::-1] + tour[j + 1:]
            yield nb


def one_point_crossover(parent1, parent2, rng):
    """DELIBERATELY BROKEN baseline. Splices the head of parent1 onto the tail of
    parent2. For a *permutation* this produces repeated / missing cities — an
    INVALID tour. ``validate_tour`` will reject it. This is the trap the plan
    wants you to hit before discovering order crossover (OX)."""
    n = len(parent1)
    cut = rng.randrange(1, n)
    return list(parent1[:cut]) + list(parent2[cut:])


def validate_tour(tour, n):
    """True iff ``tour`` is a permutation of 0..n-1. Call this on every child so
    an invalid operator is caught immediately, not after 15 min of fitness
    debugging (instructor note)."""
    return len(tour) == n and sorted(tour) == list(range(n))


def tsp_hill_climb(tsp, rng, neighbors_fn=two_opt_neighbors, max_evals=20_000, start=None):
    """First-improvement 2-opt local search with random restarts, capped at an
    EVALUATION BUDGET (each length() call is one evaluation). Restarts spend the
    remaining budget from a fresh random tour — this is what lets it escape a
    single local optimum, and why it is a strong TSP baseline."""
    evals = 0
    best_tour, best_len = None, math.inf
    first = True
    while evals < max_evals:
        cur = start if (first and start is not None) else tsp.random_tour(rng)
        first = False
        cur_len = tsp.length(cur); evals += 1
        improved = True
        while improved and evals < max_evals:
            improved = False
            for nb in neighbors_fn(cur):
                if evals >= max_evals:
                    break
                nl = tsp.length(nb); evals += 1
                if nl < cur_len - 1e-9:
                    cur, cur_len, improved = nb, nl, True
                    break                    # first-improvement
        if cur_len < best_len:
            best_tour, best_len = cur, cur_len
    return best_tour, best_len


def tsp_genetic_algorithm(tsp, crossover, mutation, rng, pop_size=50,
                          mutation_rate=0.1, tournament=5, elitism=2,
                          max_evals=20_000, use_crossover=True, record=False):
    """Generational GA with tournament selection + elitism, on an EQUAL
    EVALUATION BUDGET (NOT fixed generations — comparing at equal generations
    silently favours large populations; see notebook §6).

    ``crossover(p1, p2, rng)`` and ``mutation(tour, rng)`` are YOUR operators
    from starter.py. Set ``use_crossover=False`` for the crossover ablation."""
    n = tsp.n
    pop = [tsp.random_tour(rng) for _ in range(pop_size)]
    fit = [tsp.value(t) for t in pop]
    evals = pop_size
    best_len = min(tsp.length(t) for t in pop)
    trace = []
    while evals + pop_size <= max_evals:
        if record:
            trace.append(best_len)
        ranked = sorted(zip(fit, pop), key=lambda kv: -kv[0])
        new_pop = [list(t) for _, t in ranked[:elitism]]

        def pick():
            cands = [rng.randrange(pop_size) for _ in range(tournament)]
            return pop[max(cands, key=lambda i: fit[i])]

        while len(new_pop) < pop_size:
            p1, p2 = pick(), pick()
            child = crossover(p1, p2, rng) if use_crossover else list(p1)
            if rng.random() < mutation_rate:
                child = mutation(child, rng)
            new_pop.append(child)

        pop = new_pop
        fit = [tsp.value(t) for t in pop]
        evals += pop_size
        best_len = min(best_len, min(tsp.length(t) for t in pop))
    return best_len, trace


# ---- instance loading -------------------------------------------------------

def load_instances(path=None):
    """Load the provided TSP instance from instances.json. Returns the parsed
    dict: {seed, n_cities, cities, nearest_neighbor_tour, nearest_neighbor_length}."""
    path = Path(path or Path(__file__).with_name("instances.json"))
    return json.loads(path.read_text())


def load_tsp(path=None):
    """Convenience: build the TSP object directly from instances.json."""
    return TSP(load_instances(path)["cities"])


# =============================================================================
# Session-A reference problem: KNAPSACK (extracted VERBATIM from the notebook,
# week-10-local-search-ga.ipynb §4/§7). Not used by the studio tests — provided
# so the notebook's GA/hill-climbing demo is reproducible from a file.
# =============================================================================

def make_knapsack(n_items=100, seed=SEED):
    rng = random.Random(seed)
    weights = [rng.randint(1, 60) for _ in range(n_items)]
    values  = [rng.randint(1, 100) for _ in range(n_items)]
    cap = sum(weights) // 3
    return weights, values, cap


WEIGHTS, VALUES, CAP = make_knapsack()
MAXV = max(VALUES)


def true_value(genome):
    """What the solution is actually worth. 0 if it does not fit."""
    w = sum(x * wt for x, wt in zip(genome, WEIGHTS))
    return 0 if w > CAP else sum(x * v for x, v in zip(genome, VALUES))


def fitness(genome):
    """PENALTY fitness: overweight solutions are punished in proportion to the
    overage, not flattened to zero (see the notebook for why a hard zero makes
    the landscape flat and gives selection nothing to work with)."""
    w = sum(x * wt for x, wt in zip(genome, WEIGHTS))
    v = sum(x * val for x, val in zip(genome, VALUES))
    if w <= CAP:
        return v
    return max(0.0, v - 2.0 * MAXV * (w - CAP))


def knapsack_optimum():
    """Exact DP optimum -- so we can report % of optimum, not just 'a number'."""
    best = [0] * (CAP + 1)
    for wt, v in zip(WEIGHTS, VALUES):
        for c in range(CAP, wt - 1, -1):
            best[c] = max(best[c], best[c - wt] + v)
    return max(best)


OPT = knapsack_optimum()


def knapsack_genetic_algorithm(pop_size=60, mutation=0.02, tournament=3,
                               max_evals=20_000, elitism=2, rng=None, record=False,
                               density=0.15):
    """Verbatim knapsack GA from the notebook (renamed to avoid clashing with the
    TSP GA above). Uniform crossover + bit-flip mutation + elitism."""
    rng = rng or random.Random(SEED)
    n = len(WEIGHTS)
    pop = [[1 if rng.random() < density else 0 for _ in range(n)]
           for _ in range(pop_size)]
    evals = 0
    scores = [fitness(g) for g in pop]; evals += pop_size
    best = max(true_value(g) for g in pop)
    trace, diversity = [], []
    while evals + pop_size <= max_evals:
        if record:
            trace.append(best)
            diversity.append(len({tuple(g) for g in pop}) / pop_size)
        ranked = sorted(zip(scores, pop), key=lambda kv: -kv[0])
        new_pop = [list(g) for _, g in ranked[:elitism]]

        def pick():
            cands = [rng.randrange(pop_size) for _ in range(tournament)]
            return pop[max(cands, key=lambda i: scores[i])]

        while len(new_pop) < pop_size:
            p1, p2 = pick(), pick()
            child = [p1[i] if rng.random() < 0.5 else p2[i] for i in range(n)]
            child = [1 - b if rng.random() < mutation else b for b in child]
            new_pop.append(child)

        pop = new_pop
        scores = [fitness(g) for g in pop]; evals += pop_size
        best = max(best, max(true_value(g) for g in pop))
    return best, trace, diversity


if __name__ == "__main__":
    # Smoke test the engine on the provided instance (does not need starter.py).
    data = load_instances()
    tsp = TSP(data["cities"])
    print(f"TSP instance: {tsp.n} cities (seed {data['seed']})")
    nn = tsp.nearest_neighbor_tour()
    print(f"nearest-neighbour tour length: {tsp.length(nn):.1f}")
    print(f"stored NN tour length         : {data['nearest_neighbor_length']:.1f}")
    print(f"knapsack DP optimum (Session-A reference): {OPT}")
