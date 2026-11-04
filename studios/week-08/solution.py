"""Week 8 studio — REFERENCE SOLUTION (instructor-only).

A filled-in copy of ``starter.py``: identical function names and signatures, so
the *provided* ``test_unify.py`` passes when this module is imported in place of
``starter``. Verify with ``studios/_verify_solutions.py`` (which aliases this file
to the name ``starter`` and runs the unmodified test).

DO NOT ship this to students — it is excluded via ``studios/.gitignore``. The
teaching walkthrough lives in ``solution.ipynb`` (which imports this file rather
than re-pasting it, so the two never drift).

Two tasks:
  Task 1  ``occurs``        — rule 4 of unification. Refuse the binding when the
                              variable already appears inside the term, so
                              ``unify(X, f(X))`` fails instead of building
                              f(f(f(...))). Removing it is what makes standard
                              Prolog unsound-for-speed.
  Task 2  ``forward_chain`` — the deductive closure of the family/taxonomy KB,
                              computed to a fixpoint by matching every rule body
                              against the known facts with the GIVEN ``unify``.
"""
from unify import (
    Var, Compound, is_var, is_compound, unify, resolve,
    FACTS, RULES,
)


# ---- Task 1: the occurs check -----------------------------------------------

def occurs(var, x, theta):
    """Does ``var`` appear anywhere inside ``x``, following bindings in ``theta``?

    Instructor note: this is byte-for-byte the ``occurs`` already in ``unify.py``
    (the engine calls its own copy from ``unify_var``); students re-derive it here
    so they *own* rule 4. The three cases, in order:
      1. ``var == x``                         -> True  (found it)
      2. ``x`` is a bound variable            -> recurse into ``theta[x]``
      3. ``x`` is a compound ``f(a, b, ...)`` -> True if var occurs in ANY arg
    Everything else (a constant, a distinct unbound var) -> False.
    """
    if var == x:                                       # case 1
        return True
    if is_var(x) and x in theta:                       # case 2 — chase the binding
        return occurs(var, theta[x], theta)
    if is_compound(x):                                 # case 3 — any argument
        return any(occurs(var, a, theta) for a in x.args)
    return False


# ---- Task 2: forward chaining over the family KB ----------------------------

def _match(body, theta, facts):
    """Yield every substitution that unifies the WHOLE ``body`` against ``facts``.

    Recursive: unify the first atom against each known fact, and for every success
    recurse on the rest carrying the accumulated substitution. A *copy* of theta
    goes into each branch so siblings never clobber each other's bindings.
    """
    if not body:
        yield theta
        return
    first, rest = body[0], body[1:]
    for fact in facts:
        theta2 = unify(first, fact, dict(theta))
        if theta2 is not None:
            yield from _match(rest, theta2, facts)


def forward_chain(facts, rules):
    """Return the deductive closure of ``facts`` under ``rules`` (a set of ground
    Compound atoms), computed to a fixpoint.

    Each pass matches every rule body against a FROZEN snapshot of the current
    facts (so we never mutate the set we are iterating), adds every now-ground
    head, and repeats until a pass adds nothing new. The snapshot is why recursive
    rules like ``ancestor`` need several passes — each pass reaches one step
    further — and the fixpoint loop keeps going until it stops growing.
    """
    facts = set(facts)
    changed = True
    while changed:
        changed = False
        current = frozenset(facts)                     # match against a snapshot
        for head, body in rules:
            for theta in _match(list(body), {}, current):
                derived = resolve(head, theta)         # the now-ground head
                if derived not in facts:
                    facts.add(derived)
                    changed = True
    return facts


if __name__ == "__main__":
    print("Task 1 — occurs check:")
    print("  occurs(X, f(X), {}) =", occurs(Var("X"), Compound("f", Var("X")), {}))
    print("  occurs(X, f(Y), {}) =", occurs(Var("X"), Compound("f", Var("Y")), {}))

    print("\nTask 2 — forward chaining over the family KB:")
    closure = forward_chain(FACTS, RULES)
    derived = sorted(str(a) for a in closure - set(FACTS))
    print(f"  {len(derived)} facts derived:")
    for a in derived:
        print("   ", a)
