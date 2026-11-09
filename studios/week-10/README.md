# Week 10 Studio — Genetic Algorithms & Local Search on TSP

**Companion to** [`../../weeks/week-10.md`](../../weeks/week-10.md) — Session B.
**Time budget:** Recap 5 · Breakouts 45 · Demos 20 · Debrief 10 (80 min total).
**Deliverables:** all provided tests pass; a mean ± std table, a population × mutation
heatmap, one convergence plot with error bands, and the crossover ablation.

> **Recap (5 min).** *Why does mutation rate 0 break a GA? Why does 0.5?*
> (Rate 0: diversity collapses to a clone, crossover cannot invent a lost allele.
> Rate 0.5: it becomes random search and never converges.)

## Files in this folder

| File | Purpose | You edit it? |
|---|---|---|
| [`localsearch.py`](localsearch.py) | Given: hill climbing, simulated annealing, the `TSP` problem, 2-opt neighbourhood, the GA/hill-climb drivers, the broken `one_point_crossover` + `validate_tour`, and the notebook's knapsack code (Session-A reference) | ❌ |
| [`instances.json`](instances.json) | Given: the 30-city TSP instance + its nearest-neighbour "known-good" tour (seed 20250806) | ❌ |
| [`starter.py`](starter.py) | **Task 1** — implement `order_crossover` (OX) + `swap_mutation`; **Task 2** — fill in `run_study` | ✅ |
| [`test_localsearch.py`](test_localsearch.py) | Provided tests, incl. `test_honest_2opt_not_beaten_by_naive_ga` | ❌ |
| [`_generate_instances.py`](_generate_instances.py) | Regenerates `instances.json` (only needed if you rotate the seed) | ❌ |

> **Note on the instance.** The lesson plan promises a "30-city TSP instance
> provided", but the Session-A notebook only ever builds 8-queens and knapsack —
> there is no TSP in it. So `instances.json` is *generated reproducibly* from the
> notebook's seed (20250806), not copied. See `_generate_instances.py`.

## Task 1 — GA for TSP + provided tests (20 min)

Open `starter.py`. Implement two operators, then run:

```bash
python3 test_localsearch.py
```

- `swap_mutation(tour, rng)` — exchange two positions. A swap can never create a
  duplicate, so the result is always a valid tour.
- `order_crossover(parent1, parent2, rng)` — **this is the point of Task 1.** Try
  it with plain one-point crossover first (`localsearch.one_point_crossover` is
  provided, deliberately broken) and watch `validate_tour` reject the children:
  splicing two permutations produces repeated/missing cities. Then fix it with
  **order crossover (OX)** — copy a segment from parent1, fill the rest from
  parent2 in order, skipping cities already taken. Write `validate_tour()` checks
  *first* so invalidity shows up immediately, not after 15 min of fitness debugging.

The GA driver (`tsp_genetic_algorithm`) is given — it calls *your* operators. It
also does tournament selection, elitism, and — critically — runs to a fixed
**evaluation budget**, not a fixed number of generations (see Task 2).

**The failing-guarantee test.** `test_honest_2opt_not_beaten_by_naive_ga` asserts
that at equal budget, 2-opt hill climbing (given, `tsp_hill_climb`) is *not* beaten
by your naive GA — it wins on average across seeds. This is not a bug. **A GA is
not automatically better for being biologically inspired.** On TSP with a proper
2-opt neighbourhood, simple local search frequently wins at equal budget. The
studio asks you to check, not to assume — and reporting the honest result is worth
more than a tidy win.

## Task 2 — A real hyperparameter study (20 min)

Fill in `run_study()`. Vary **population (20, 50, 100) × mutation rate
(0.001, 0.01, 0.1) × tournament (2, 5)** — 18 configs — with **five seeds each**,
at a **fixed evaluation budget** (`max_evals`, default 20 000).

> **The methodological rule that makes this valid:** fixed *evaluations*, not
> fixed *generations*. Population 100 for 50 generations and population 20 for 250
> generations are the *same compute*. Compare at equal generations and you
> silently hand the win to large populations. The driver already counts
> evaluations; do not "fix" it to count generations.

Deliverables:

- **Table:** mean ± std best tour length per configuration.
- **Heatmap:** population × mutation rate.
- **One convergence plot** with error bands (use the `record=True` trace).
- **Crossover ablation:** rerun with `use_crossover=False`. Does crossover help on
  *this* problem? Answer with data, and connect it to the schema-theorem
  discussion. Two configurations whose error bars overlap are not distinguishable
  by this experiment — saying so is a stronger result than picking a winner.

Baselines to compare against (all in `localsearch.py`): random tours
(`TSP.random_tour`), the nearest-neighbour tour (`TSP.nearest_neighbor_tour`, also
stored in `instances.json`), and 2-opt hill climbing (`tsp_hill_climb`).

## Task 3 — Failure Atlas + notes (5 min)

Add today's entries: the OX-vs-one-point invalidity, the mutation-rate collapse
(0.0) and dissolution (0.5), and the equal-generations-vs-equal-evaluations trap.

## Demos (20 min)

Two pairs: one on the **crossover ablation**, one on the **GA-vs-2-opt**
comparison. If any pair reports a single-run result without variance, run their
config live with a different seed and show the number change — a stochastic
algorithm reported from one run is an anecdote, not a result.

## Debrief (10 min)

- Local search trades guarantees for the ability to work where systematic search
  cannot go (continuous or enormous spaces).
- SA's convergence guarantee is real and practically unreachable ("sufficiently
  slow" = slower than you can afford). Precision about *which* guarantee you hold
  is scorecard axis 2.
- GAs are a design space, not an algorithm. Most of the performance is in the
  choices, not the metaphor.
- **No LLM comparison this week, by design** — week 11 does the budget-normalized
  bake-off, and today's methodology (error bars, equal budget) is what makes that
  comparison honest.

## Links

- Session A notebook — [`../../notebooks/week-10-local-search-ga.ipynb`](../../notebooks/week-10-local-search-ga.ipynb)
- Lesson plan — [`../../weeks/week-10.md`](../../weeks/week-10.md)
- Slides — [`../../slides/week-10/deck.md`](../../slides/week-10/deck.md)
- AI policy (`AI_LOG.md`) — [`../../resources/ai-policy.md`](../../resources/ai-policy.md)
