"""Week 9 studio — REFERENCE SOLUTION (instructor-only).

A filled-in copy of ``starter.py``: identical function names and signatures, so
the *provided* ``test_planning.py`` passes when this module is imported in place
of ``starter``. Verify with ``studios/_verify_solutions.py``.

DO NOT ship this to students — excluded via ``studios/.gitignore``. The teaching
walkthrough lives in ``solution.ipynb`` (which imports this file, never re-pastes
it).

Two tasks; the engine (planner, heuristics, and the sound ``verify``) is GIVEN:
  Task 1  ``gripper_actions`` / ``gripper_problem`` — formalize the GRIPPER
          domain into ground STRIPS actions so the GIVEN planner/verifier run on
          it unchanged. Omit a precondition and the planner faithfully hands you a
          physically-impossible "valid" plan — faithful to the model, not the
          world.
  Task 2  ``refine_with_verifier`` — arm D: propose -> verify -> feed only the
          solver's error back -> retry. Correctness comes from ``verify()``, never
          from trusting the generator. That is the whole thesis of the course.
"""
from strips import Action, PlanningProblem, verify, plan  # noqa: F401


# ============================================================================
# Task 1 — the GRIPPER domain.                          [Breakout Task 1]
# ============================================================================
ROOMS = ("a", "b")
GRIPPERS = ("left", "right")


def gripper_actions(balls):
    """Every ground action of the GRIPPER domain, built once (mirrors
    ``blocks_actions``): ordered room pairs for ``move``, and every
    (ball, room, gripper) combination for ``pick``/``drop``.

    Names are spelled exactly ``move(a,b)``, ``pick(b1,a,left)``,
    ``drop(b1,b,left)`` so ``verify()``'s error messages read cleanly.
    """
    acts = []
    for frm in ROOMS:
        for to in ROOMS:
            if frm == to:
                continue
            acts.append(Action(
                f"move({frm},{to})",
                frozenset({f"at-robby({frm})"}),        # pre
                frozenset({f"at-robby({to})"}),         # add
                frozenset({f"at-robby({frm})"})))       # del
    for ball in balls:
        for room in ROOMS:
            for g in GRIPPERS:
                acts.append(Action(
                    f"pick({ball},{room},{g})",
                    frozenset({f"at({ball},{room})", f"at-robby({room})", f"free({g})"}),
                    frozenset({f"carry({ball},{g})"}),
                    frozenset({f"at({ball},{room})", f"free({g})"})))
                acts.append(Action(
                    f"drop({ball},{room},{g})",
                    frozenset({f"carry({ball},{g})", f"at-robby({room})"}),
                    frozenset({f"at({ball},{room})", f"free({g})"}),
                    frozenset({f"carry({ball},{g})"})))
    return acts


def gripper_problem(n_balls):
    """All ``n_balls`` start in room 'a'; goal is every ball in room 'b'. Robby
    starts in room 'a' with both grippers free."""
    balls = [f"b{i}" for i in range(1, n_balls + 1)]
    init = ({"at-robby(a)"}
            | {f"at({b},a)" for b in balls}
            | {f"free({g})" for g in GRIPPERS})
    goal = {f"at({b},b)" for b in balls}
    return PlanningProblem(init, goal, gripper_actions(balls))


# ============================================================================
# Task 2 — LLM-Modulo, arm D.                           [Breakout Task 2]
# ============================================================================

def refine_with_verifier(propose, problem, max_retries=3):
    """Arm D: propose -> verify -> feed the error back -> retry, up to
    ``max_retries`` attempts.

    Returns ``(plan, log)`` where ``plan`` is the FIRST proposal ``verify()``
    accepts (or None if none did within the budget), and ``log`` is a list of
    ``(attempt_number, ok, error)`` tuples, one per attempt.

    The correctness decision is entirely ``verify()``'s: we never trust the
    generator, and we feed back ONLY the solver's error string (``last_error``),
    never a ground-truth answer — leaking the answer would invalidate the arm.
    """
    log = []
    last_error = None
    for attempt in range(max_retries):
        proposal = propose(problem, attempt, last_error)
        ok, err = verify(proposal, problem)
        log.append((attempt + 1, ok, err))
        if ok:
            return proposal, log
        last_error = err                    # only the error is fed back
    return None, log


if __name__ == "__main__":
    prob = gripper_problem(2)
    result, exp = plan(prob, "add")
    print(f"gripper(2) plan ({len(result)} steps, {exp} expansions):")
    for i, a in enumerate(result, 1):
        print(f"  {i}. {a}")
    print("verify:", verify(result, prob))
