"""Week 9 studio — starter (STRIPS domain + the LLM-Modulo refinement loop).

You fill in TWO things. Everything else — the planner, the heuristics, and the
sound ``verify()`` — is GIVEN in ``strips.py`` and must not change.

    Task 1  (Breakout Task 1): formalize the GRIPPER domain into STRIPS.
    Task 2  (Breakout Task 2, arm D): the verifier-in-the-loop refinement loop.

Then run ``python3 test_planning.py``. All tests must pass, including the
*guarantee* test that watches a confident-but-wrong plan get rejected — because
a guarantee you cannot watch enforce itself is not one you have understood.
"""
from strips import Action, PlanningProblem, verify, plan  # noqa: F401


# ============================================================================
# Task 1 — Write a domain (15 min).                    [Breakout Task 1]
# ============================================================================
# The notebook gave you Blocks World. Now formalize a DIFFERENT domain so you
# feel representation choices bite. We use GRIPPER — a robot with two grippers
# ferries balls between two rooms. Same trick as blocks_actions: build the
# ground Action list; the GIVEN planner and verifier then work UNCHANGED.
#
# Objects:  rooms  "a", "b"        (robby starts in room "a")
#           balls  "b1", "b2", ...
#           grippers "left", "right"
#
# Fluents (strings, exactly as written here — the goal is built from them):
#     at-robby(<room>)             robby is in that room
#     at(<ball>,<room>)            that ball is resting in that room
#     free(<gripper>)              that gripper is empty
#     carry(<ball>,<gripper>)      that ball is held by that gripper
#
# Action schemas (fill the three sets for each; mirror blocks_actions):
#     move(<from>,<to>)
#         pre: at-robby(from)
#         add: at-robby(to)              del: at-robby(from)
#     pick(<ball>,<room>,<gripper>)
#         pre: at(ball,room), at-robby(room), free(gripper)
#         add: carry(ball,gripper)       del: at(ball,room), free(gripper)
#     drop(<ball>,<room>,<gripper>)
#         pre: carry(ball,gripper), at-robby(room)
#         add: at(ball,room), free(gripper)   del: carry(ball,gripper)
#
# Name actions exactly "move(a,b)", "pick(b1,a,left)", "drop(b1,b,left)" so
# verify()'s error messages read cleanly.

ROOMS = ("a", "b")
GRIPPERS = ("left", "right")


def gripper_actions(balls):
    """The GRIPPER DOMAIN: every ground action, written once, reused per problem.

    ``balls`` is an iterable of ball names, e.g. ("b1", "b2").
    Return a list[Action]. See the schemas in the module docstring above.
    """
    # TODO: build move(...) over ordered room pairs, then pick(...)/drop(...)
    #       over every (ball, room, gripper) combination. Follow blocks_actions.
    raise NotImplementedError


def gripper_problem(n_balls):
    """All ``n_balls`` start in room 'a'; goal is every ball in room 'b'.

    Robby starts in room 'a' with both grippers free.
    """
    balls = [f"b{i}" for i in range(1, n_balls + 1)]
    # TODO: build the init set (at-robby(a); every ball at(a); every gripper free)
    #       and the goal set (every ball at(b)), then return a PlanningProblem
    #       over gripper_actions(balls).
    raise NotImplementedError


# ============================================================================
# Task 2 — LLM-Modulo, arm D (25 min).                 [Breakout Task 2]
# ============================================================================
# Arm D is the point of the week: the LLM PROPOSES a plan, the sound verify()
# CHECKS it, and on failure the error message (only the error — never the
# answer) is fed back for a retry. The guarantee lives in verify(), which is
# GIVEN. You write the loop that USES it.
#
# ``propose`` is your (possibly unreliable) generator. It is called as
#     propose(problem, attempt, last_error)
# and returns a list of action-name strings. ``last_error`` is None on the
# first attempt, otherwise verify()'s first_error string from the previous try.

def refine_with_verifier(propose, problem, max_retries=3):
    """Arm D: propose -> verify -> feed error back -> retry, up to max_retries.

    Return ``(plan, log)`` where ``plan`` is the FIRST proposal verify() accepts
    (or None if none did within the budget), and ``log`` is a list of
    ``(attempt_number, ok, error)`` tuples, one per attempt.

    Correctness must come from verify(), never from trusting ``propose``.
    """
    # TODO: loop attempt = 0 .. max_retries-1; call propose(...); ok, err =
    #       verify(proposal, problem); append (attempt+1, ok, err) to the log;
    #       return (proposal, log) on the first ok; else carry err into
    #       last_error and keep going. Return (None, log) if the budget runs out.
    raise NotImplementedError


if __name__ == "__main__":
    # Quick smoke test once Task 1 is filled in.
    prob = gripper_problem(2)
    result, exp = plan(prob, "add")
    print(f"gripper(2) plan ({len(result)} steps, {exp} expansions):")
    for i, a in enumerate(result, 1):
        print(f"  {i}. {a}")
    print("verify:", verify(result, prob))
