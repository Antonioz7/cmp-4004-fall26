# Week 9 Studio — LLM-Modulo: Where the Guarantee Comes From

**Companion to** [`../../weeks/week-09.md`](../../weeks/week-09.md) — Session 9B.
**Time budget:** Recap 5 · Breakouts 45 · Demos 20 · Debrief 10 (80 min total).
**Deliverables:** all provided tests pass, a domain you formalized yourself, and a
valid-plan-rate plot for the four-arm experiment (arm C vs. arm D).

> **Duel 2 (The Formalizer) is due this week — Session 9A.** This studio is the
> live rehearsal of the exact architecture the duel grades: an LLM proposes, a
> **sound solver verifies**. Spec: [`../../projects/duel-2-formalizer.md`](../../projects/duel-2-formalizer.md).

> **Recap (5 min).** *What does the delete-relaxation ignore, and why is the
> result still useful?* Cold-call. If nobody has it: it drops every delete effect,
> so nothing can be undone and the relaxed problem is polynomial — and the heuristic
> is still informative because reaching a fluent at all is most of the work.

## Files in this folder

| File | Purpose | You edit it? |
|---|---|---|
| [`strips.py`](strips.py) | Given: `Action`, `applicable`/`apply_action`, `blocks_actions`, `PlanningProblem`, `h_add`/`h_max`, `astar`, `plan`, and **`verify()`** — copied verbatim from the notebook | ❌ |
| [`starter.py`](starter.py) | **Task 1** (formalize the Gripper domain) and **Task 2** (arm-D refinement loop) | ✅ |
| [`test_planning.py`](test_planning.py) | Provided tests, incl. `test_unverified_wrong_plan_is_never_accepted` | ❌ |

`astar` in `strips.py` is **week 4's function, unmodified** — only the
representation and the (auto-derived) heuristic changed. The problem *data* is not
a seeded JSON bank like weeks 3–4: the notebook generates it procedurally, so the
instances are whatever `blocks_problem(n)` and your `gripper_problem(n)` produce.

## ⚠️ `verify()` is GIVEN, not a TODO

`verify()` is the keystone of the entire course thesis — an unreliable generator
plus a **sound** verifier is a reliable system. It is an oracle you are handed, not
an exercise. It replays a plan against the model, checks every precondition and the
goal, and returns `(ok, first_error)`. Read it, trust it, and feed its error string
back to your generator. **Do not reimplement it.** Everything in `strips.py` is
frozen.

## Task 1 — Write a domain (15 min)  ·  [Breakout Task 1]

The notebook gave you Blocks World. Formalize a **different** domain so representation
choices bite: fill in `gripper_actions(balls)` and `gripper_problem(n_balls)` in
`starter.py`. A two-gripper robot ferries balls between two rooms. Build the ground
`Action` list exactly as `blocks_actions` does; the **given** planner and verifier
then run on it *unchanged* — that reuse is the week's payoff (domain written once,
problems unlimited, heuristic derived automatically).

The reliable failure: omit a precondition and the planner will hand you a "valid"
plan that is physically nonsense (two balls in one gripper, or two blocks in one
hand — see the notebook's final cell). **The planner is faithful to the model you
wrote, not to the world you meant.** Name it out loud when it happens to you.

## Task 2 — LLM-Modulo, arm D (25 min)  ·  [Breakout Task 2]

Four arms this time — the fourth is what makes this the course's key experiment.
Run 15 Blocks World problems across sizes **3, 5, 7, 9** (`blocks_problem(n)`):

| Arm | Pipeline |
|---|---|
| **A** | Hand-written domain → `plan()` |
| **B** | LLM writes the **problem** file (domain given) → `plan()` |
| **C** | LLM outputs a plan **directly** |
| **D** | **LLM proposes → `verify()` checks → error fed back → retry (max 3)** |

Arm D is `refine_with_verifier(propose, problem, max_retries=3)` in `starter.py`,
and writing it is the point. Your `propose(problem, attempt, last_error)` is the
generator (`aicourse.llm.LLM`, or the simulated one in the notebook's §9 so you can
watch the loop without burning tokens). The loop must take its correctness from
`verify()`, never from trusting the proposal — **and only the solver's error may be
fed back, never a ground-truth answer** (leaking it invalidates the arm; see the
Duel 2 notes).

```python
from aicourse.llm import LLM          # or the fake generator from notebook §9
from strips import blocks_problem, plan, verify
from starter import refine_with_verifier

rows = []
for n in (3, 5, 7, 9):
    prob = blocks_problem(n)
    plan_d, log = refine_with_verifier(make_propose(LLM(), prob), prob)
    rows.append((n, "D", plan_d is not None, len(log)))
    # arm C: verify(model_plan_directly(prob), prob) — no retries
```

Required measurements (mirror Duel 2's instrumentation):

- **Valid-plan rate per arm, per size — plot it** (four sizes, so the cliff shows).
- Optimality rate (plan length vs. `plan()`'s length).
- Arm D: iterations to a valid plan; fraction that never converge in 3.
- Arm B: PDDL syntax errors vs. semantically-wrong problem files.
- Cost per *solved* instance (tokens + planner time).

Then run:

```bash
python3 test_planning.py
```

All six must pass. The two to read carefully both encode the thesis:

- `test_verify_rejects_every_kind_of_wrong_plan` — the **given** verifier localises
  and rejects a hallucinated action, an unmet precondition, and an incomplete plan.
- `test_unverified_wrong_plan_is_never_accepted` — a **confident, wrong** generator
  never gets its plan certified. A guarantee you cannot watch enforce itself is one
  you have not understood.

## Task 3 — Scorecard (5 min)

Four columns (A, B, C, D). Add the categorical row that has *no LLM analogue*: a
planner **proves** an impossible goal (`on(a,b) ∧ on(b,a)`) has no plan by
exhaustion — that is a theorem, not a percentage (notebook §7).

## Demos (20 min)

Ask specifically for the **arm C vs. arm D** plot. The expected shape is stark: arm
C degrades sharply with block count; arm D climbs back toward arm A — *because the
verifier is sound*. Three pairs replicating the same curve stops it being anecdote.
Then the question that makes the week land:

> In arm D, where does the guarantee come from?

Push until someone says it precisely: **the verifier.** The LLM's output is a
*proposal*; correctness comes from a sound checker that would reject a wrong plan no
matter how confidently it was produced.

## Debrief (10 min)

- STRIPS's factored representation is what makes automatic heuristic derivation
  possible — `h_add` never mentions blocks and would work on Gripper unchanged.
- Kambhampati's framing, now earned: LLMs are poor autonomous planners and useful
  *within* a verified loop. Arm C is the one nobody should ship.
- **The generalization:** classical AI supplies verifiers. An unreliable generator
  plus a sound verifier is a reliable system. That is the answer to "why learn this
  if LLMs exist" — and it is the single most transferable idea in the course.
- The limit (notebook §11): a sound verifier protects you from a bad **generator**,
  not from a bad **specification**. Do not oversell verification in your capstone.

## Links

- Session 9A notebook — [`../../notebooks/week-09-planning.ipynb`](../../notebooks/week-09-planning.ipynb)
- Slides — [`../../slides/week-09/deck.md`](../../slides/week-09/deck.md)
- Duel 2 spec (this architecture, graded) — [`../../projects/duel-2-formalizer.md`](../../projects/duel-2-formalizer.md)
- Duel scorecard — [`../../resources/duel-scorecard.md`](../../resources/duel-scorecard.md)
- AI policy (`AI_LOG.md`) — [`../../resources/ai-policy.md`](../../resources/ai-policy.md)
