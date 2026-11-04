"""Provided tests for the week-9 studio.

Run: ``python3 test_planning.py``. Prints one line per test.

Two tests exercise the GIVEN engine directly (they pass before you touch
anything) and are the course's central thesis, as tests:

    test_verify_rejects_every_kind_of_wrong_plan
        — the sound verifier localises and rejects a hallucinated action, an
          unmet precondition, and an incomplete plan.
    test_unverified_wrong_plan_is_never_accepted
        — an unreliable generator that is CONFIDENT and WRONG never gets its
          plan certified, because correctness comes from verify(), not from the
          generator. This is "an unreliable generator + a sound verifier is a
          reliable system," reduced to an assertion.

The rest depend on your Task 1 (gripper domain) and Task 2 (refinement loop).
"""
import sys

from strips import blocks_problem, plan, verify
import starter as s


# ---- Task-independent: the GIVEN verifier is the oracle ---------------------

def test_verify_accepts_a_valid_plan():
    p = blocks_problem(3)
    good, _ = plan(p, "add")
    ok, err = verify(good, p)
    assert ok and err is None, f"verify rejected a planner-produced plan: {err}"
    print("  ok  verify() accepts a valid plan and reports no error")


def test_verify_rejects_every_kind_of_wrong_plan():
    p = blocks_problem(3)
    good, _ = plan(p, "add")

    ok, err = verify(["teleport(a,b)"], p)              # hallucinated action
    assert not ok and "unknown action" in err, err

    ok, err = verify(["stack(a,b)"], p)                 # precondition not met
    assert not ok and "needs" in err, err

    ok, err = verify(good[:-1], p)                      # stops one step short
    assert not ok and "goal not reached" in err, err

    print("  ok  verify() rejects hallucinated / bad-precond / incomplete plans")


# ---- Task 1: the gripper domain --------------------------------------------

def test_gripper_domain_is_solvable_and_verifies():
    p = s.gripper_problem(2)
    result, _ = plan(p, "add")
    assert result is not None, "planner found no plan for gripper(2) — check schemas"
    ok, err = verify(result, p)
    assert ok, f"planner's own plan failed verify() on gripper(2): {err}"
    print(f"  ok  gripper(2) solved in {len(result)} steps and verify() accepts it")


def test_gripper_goal_requires_moving_every_ball():
    # A hand-written non-plan (robby just wanders) must NOT reach the goal.
    p = s.gripper_problem(2)
    ok, err = verify(["move(a,b)", "move(b,a)"], p)
    assert not ok and "goal not reached" in err, (
        f"empty ferrying wrongly accepted for gripper(2): {(ok, err)}"
    )
    print("  ok  gripper goal is not reached without actually ferrying the balls")


# ---- Task 2: arm D, the verifier-in-the-loop refinement --------------------

def _flaky_generator(problem):
    """Stands in for an LLM: wrong, then incomplete, then finally correct."""
    correct = [a.name for a in plan(problem, "add")[0]]

    def propose(prob, attempt, last_error):
        if attempt == 0:
            return ["stack(a,b)"] + correct        # missing the pick-up
        if attempt == 1:
            return correct[:-1]                    # stops one short
        return correct                             # finally right
    return propose


def _confidently_wrong_generator(problem):
    """Always returns a legal-but-goal-missing plan, no matter the feedback."""
    def propose(prob, attempt, last_error):
        return ["pick-up(a)", "put-down(a)"]       # applies fine, wrong goal
    return propose


def test_refinement_loop_converges_and_returns_a_verified_plan():
    p = blocks_problem(3)
    final, log = s.refine_with_verifier(_flaky_generator(p), p, max_retries=3)
    assert final is not None, "loop gave up on a generator that does converge"
    ok, err = verify(final, p)
    assert ok, f"loop returned a plan verify() rejects: {err}"
    assert log[-1][1] is True, f"log doesn't record the accepting attempt: {log}"
    assert len(log) == 3, f"expected 3 attempts (wrong, incomplete, right), got {log}"
    print(f"  ok  arm-D loop converged on attempt {len(log)} to a verified plan")


def test_unverified_wrong_plan_is_never_accepted():
    """THE thesis. A confident, wrong generator never gets certified."""
    p = blocks_problem(3)
    final, log = s.refine_with_verifier(_confidently_wrong_generator(p), p,
                                        max_retries=3)
    assert final is None, (
        "loop CERTIFIED a plan from a generator that never reaches the goal — "
        "the guarantee must come from verify(), not from trusting the generator"
    )
    assert all(ok is False for _, ok, _ in log), f"a wrong plan slipped through: {log}"
    print("  ok  a confident-but-wrong generator is never certified (verify() holds)")


TESTS = [
    test_verify_accepts_a_valid_plan,
    test_verify_rejects_every_kind_of_wrong_plan,
    test_gripper_domain_is_solvable_and_verifies,
    test_gripper_goal_requires_moving_every_ball,
    test_refinement_loop_converges_and_returns_a_verified_plan,
    test_unverified_wrong_plan_is_never_accepted,
]


def main():
    failed = 0
    for t in TESTS:
        try:
            t()
        except NotImplementedError:
            print(f"  --  {t.__name__}: starter not implemented yet")
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
