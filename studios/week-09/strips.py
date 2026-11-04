"""Week 9 studio — the shared STRIPS engine (GIVEN to you; do not modify).

This is the planner from the Session-A notebook, unchanged. Week 9 is about
*representation* and *sound verification*, not about re-implementing search — so
the engine is provided. You write the domain and the refinement loop in
``starter.py``.

Everything here is copied verbatim from ``notebooks/week-09-planning.ipynb``:

    Action / applicable / apply_action     — actions as three sets of fluents
    PlanningProblem / blocks_problem        — week 3's interface, unchanged
    blocks_actions                          — the Blocks World DOMAIN (schemas)
    h_add / h_max                           — heuristics DERIVED from the domain
    astar                                   — week 4's A*, IDENTICAL
    plan                                    — astar + a derived heuristic
    verify                                  — ⚠️ the sound plan validator

``verify()`` is the keystone of the whole course thesis (an unreliable generator
plus a sound verifier is a reliable system). **It is GIVEN — an oracle, not a
TODO.** Read it, trust it, feed its error messages back to your generator; do not
reimplement it.
"""
import heapq
import itertools  # noqa: F401  (kept to match the notebook's imports)
import time  # noqa: F401
from dataclasses import dataclass


@dataclass(frozen=True)
class Action:
    name: str
    precond: frozenset
    add: frozenset
    delete: frozenset

    def __repr__(self):
        return self.name


def applicable(action, state):
    return action.precond <= state           # set containment. That is all.


def apply_action(action, state):
    return (state - action.delete) | action.add


# --- Blocks World domain -------------------------------------------------
def blocks_actions(blocks):
    """The DOMAIN: written once, reused for every problem instance."""
    acts = []
    for b in blocks:
        acts.append(Action(f"pick-up({b})",
                           frozenset({f"clear({b})", f"ontable({b})", "handempty"}),
                           frozenset({f"holding({b})"}),
                           frozenset({f"clear({b})", f"ontable({b})", "handempty"})))
        acts.append(Action(f"put-down({b})",
                           frozenset({f"holding({b})"}),
                           frozenset({f"clear({b})", f"ontable({b})", "handempty"}),
                           frozenset({f"holding({b})"})))
        for c in blocks:
            if b == c:
                continue
            acts.append(Action(f"stack({b},{c})",
                               frozenset({f"holding({b})", f"clear({c})"}),
                               frozenset({"handempty", f"clear({b})", f"on({b},{c})"}),
                               frozenset({f"holding({b})", f"clear({c})"})))
            acts.append(Action(f"unstack({b},{c})",
                               frozenset({f"on({b},{c})", f"clear({b})", "handempty"}),
                               frozenset({f"holding({b})", f"clear({c})"}),
                               frozenset({f"on({b},{c})", f"clear({b})", "handempty"})))
    return acts


class PlanningProblem:
    def __init__(self, initial, goal, actions):
        self.initial = frozenset(initial)
        self.goal = frozenset(goal)
        self.action_list = actions

    def actions(self, state):
        return [a for a in self.action_list if applicable(a, state)]

    def result(self, state, action):
        return apply_action(action, state)

    def is_goal(self, state):
        return self.goal <= state

    def step_cost(self, state, action):
        return 1


def blocks_problem(n_blocks):
    """Stack n blocks into a single tower a-on-b-on-c-... from a flat table."""
    bl = "abcdefghij"[:n_blocks]
    init = {f"ontable({b})" for b in bl} | {f"clear({b})" for b in bl} | {"handempty"}
    goal = {f"on({bl[i]},{bl[i+1]})" for i in range(len(bl) - 1)}
    return PlanningProblem(init, goal, blocks_actions(bl))


# --- the delete-relaxation heuristics — derived, not written -------------
def h_add(state, goal, actions):
    """Sum over goal fluents of their relaxed reachability cost. NOT admissible
    (double-counts shared subgoals) but very informative."""
    cost = {f: 0 for f in state}
    changed = True
    while changed:
        changed = False
        for a in actions:
            if a.precond <= set(cost):
                c = 1 + sum(cost[p] for p in a.precond)
                for fl in a.add:                    # add effects only -- relaxed
                    if c < cost.get(fl, float("inf")):
                        cost[fl] = c
                        changed = True
    if not goal <= set(cost):
        return float("inf")                          # unreachable even relaxed
    return sum(cost[g] for g in goal)


def h_max(state, goal, actions):
    """Cost of the most expensive goal fluent. ADMISSIBLE."""
    cost = {f: 0 for f in state}
    changed = True
    while changed:
        changed = False
        for a in actions:
            if a.precond <= set(cost):
                c = 1 + max((cost[p] for p in a.precond), default=0)
                for fl in a.add:
                    if c < cost.get(fl, float("inf")):
                        cost[fl] = c
                        changed = True
    if not goal <= set(cost):
        return float("inf")
    return max((cost[g] for g in goal), default=0)


# --- week 4's A*, unmodified ---------------------------------------------
def astar(problem, h):
    """IDENTICAL to week 4's astar. Not a variant -- the same code."""
    start = (h(problem.initial), 0, problem.initial, None, None, 0)
    frontier = [start]
    best_g = {problem.initial: 0}
    parents = {}
    expansions, tiebreak = 0, 0

    while frontier:
        f, _, state, parent, action, g = heapq.heappop(frontier)
        if state in parents and g > best_g.get(state, float("inf")):
            continue
        parents[state] = (parent, action)
        if problem.is_goal(state):
            plan = []
            while action is not None:
                plan.append(action)
                parent, action = parents[parent]
            return plan[::-1], expansions
        expansions += 1
        for a in problem.actions(state):
            s2 = problem.result(state, a)
            g2 = g + problem.step_cost(state, a)
            if g2 < best_g.get(s2, float("inf")):
                best_g[s2] = g2
                tiebreak += 1
                heapq.heappush(frontier, (g2 + h(s2), tiebreak, s2, state, a, g2))
    return None, expansions


def plan(problem, heuristic="add"):
    hf = {"add": h_add, "max": h_max,
          "zero": lambda s, g, a: 0}[heuristic]
    return astar(problem, lambda s: hf(s, problem.goal, problem.action_list))


# --- ⚠️ the sound verifier — 15 lines that carry the whole course --------
def verify(plan_steps, problem):
    """Sound plan validator. Returns (ok, first_error).

    GIVEN — this is the course's oracle. It NEVER trusts the plan's source: it
    replays the plan against the model and checks every precondition and the
    goal. Feed ``first_error`` back to your generator in arm D.
    """
    state = problem.initial
    ground = {a.name: a for a in problem.action_list}
    for i, step in enumerate(plan_steps):
        name = step if isinstance(step, str) else step.name
        if name not in ground:
            return False, f"step {i}: unknown action {name!r}"
        action = ground[name]
        if not applicable(action, state):
            missing = sorted(action.precond - state)
            return False, f"step {i}: {name} needs {missing}"
        state = apply_action(action, state)
    if not problem.goal <= state:
        return False, f"goal not reached; missing {sorted(problem.goal - state)}"
    return True, None


if __name__ == "__main__":
    # Smoke test: solve a 3-block tower, then watch verify() reject bad plans.
    p = blocks_problem(3)
    good, exp = plan(p, "add")
    print(f"plan ({len(good)} steps, {exp} expansions):")
    for i, a in enumerate(good, 1):
        print(f"  {i}. {a}")
    print("\nverify(good)       :", verify(good, p))
    print("verify(hallucinated):", verify(["teleport(a,b)"], p))
    print("verify(bad precond) :", verify(["stack(a,b)"], p))
    print("verify(incomplete)  :", verify(good[:-1], p))
