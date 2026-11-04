---
marp: true
theme: default
paginate: true
header: 'CMP-4004 · Week 9 · Knowledge Representation & Planning'
---

<!--
==============================================================================
NO SOURCE DECK EXISTS FOR THIS WEEK.
05_Planning.pptx is titled "Knowledge, Reasoning, and Planning" but stops at
unification (slide 13). This deck is written from scratch and fills the
syllabus's largest gap. See ../../resources/coverage-map.md §5.
There is therefore no slides/week-09/images/ directory. All figures here are
ASCII/text by design — nothing is missing.
==============================================================================
Week 9 Session A. Mini-lecture budget: 25 minutes. Beats per lesson plan:
why planning ≠ search (4) → PDDL (8) → frame problem (4) → automatic
heuristics (6) → progression vs. regression (3).
THIS IS THE INTELLECTUAL PEAK OF THE COURSE. Do not compress it.
DUEL 2 IS DUE THIS WEEK. Lesson plan: ../../weeks/week-09.md
-->

# Knowledge Representation and Planning

## Where the guarantee comes from

**CMP-4004** · Week 9

---

# You already have A*. Why do you need this?

Blocks World with 10 blocks has about **60 million states**.

You could, in principle, run A* on it. Two things stop you:

1. You cannot write a useful **heuristic** for an atomic state — there is nothing
   to look at.
2. You cannot even **enumerate the actions** without knowing the structure of the
   state.

> ## Representation is what enables *automatic* heuristic derivation.

That is this week's thesis, and it is the strongest argument in the course for
caring about how you write a problem down.

---

# Planning *is* search — over a different representation

| | Weeks 3–4 search | Planning |
|---|---|---|
| State | **atomic** — a blob | **set of true fluents** |
| Actions | enumerated per problem | **schemas** with variables |
| Heuristic | hand-written per domain | **derived automatically** |
| Reusability | none | **domain reused across all problems** |

The third row is the payoff. `h_max`, `h_add`, and `h_FF` are computed **from the
domain description**. You write no heuristic at all.

*This is deck 03's atomic → factored → structured axis, cashed in.*

<!--
4 min. Row 3 is the one to dwell on. In week 4 students invented heuristics by
hand via relaxation; here the machine does the relaxation for them, using the
same principle. Make that connection explicit — it is what makes the result feel
inevitable rather than magical.
-->

---

# PDDL — the domain

```lisp
(define (domain blocks)
  (:requirements :strips :typing)
  (:types block)
  (:predicates (on ?x - block ?y - block)
               (ontable ?x - block)
               (clear ?x - block)
               (holding ?x - block)
               (handempty))

  (:action pick-up
    :parameters (?x - block)
    :precondition (and (clear ?x) (ontable ?x) (handempty))
    :effect (and (holding ?x)
                 (not (clear ?x))
                 (not (ontable ?x))
                 (not (handempty))))

  (:action stack
    :parameters (?x - block ?y - block)
    :precondition (and (holding ?x) (clear ?y))
    :effect (and (handempty) (clear ?x) (on ?x ?y)
                 (not (holding ?x)) (not (clear ?y)))))
```

---

# PDDL — the problem

```lisp
(define (problem blocks-3)
  (:domain blocks)
  (:objects a b c - block)
  (:init (ontable a) (ontable b) (ontable c)
         (clear a) (clear b) (clear c) (handempty))
  (:goal (and (on a b) (on b c))))
```

## The separation is the point

**The domain is written once. The problems are unlimited.**

No search algorithm from weeks 3–5 has that property. Your 8-puzzle code solves
8-puzzles; this domain file solves every Blocks World instance anyone ever writes.

<!--
8 min for the two PDDL slides. Write the domain LIVE, explaining each part. The
anatomy — preconditions / add effects / delete effects — is what the frame
problem slide depends on.
-->

---

# Action anatomy, in STRIPS terms

For `pick-up(a)`:

| | |
|---|---|
| **Preconditions** | `clear(a)`, `ontable(a)`, `handempty` |
| **Add list** | `holding(a)` |
| **Delete list** | `clear(a)`, `ontable(a)`, `handempty` |

Applying an action is set arithmetic:

```python
def applicable(action, state):
    return action.precond <= state           # set containment

def apply_action(action, state):
    return (state - action.delete) | action.add
```

Two lines. That is the whole transition model, for every action in every domain.

---

# The frame problem

## Ask: what does `pick-up(a)` do to `(ontable b)`?

## Nothing. And *nothing was written down.*

**That silence is the solution.** STRIPS assumes: anything not in the add or
delete list **persists**.

### The alternative, in pure logic

```
∀x (x ≠ a → (ontable(x, s) → ontable(x, Result(pickup(a), s))))
```

One axiom **per predicate per action** — O(A × F) frame axioms, all of them
saying "nothing happened."

### Does STRIPS *solve* the frame problem, or sidestep it?

It sidesteps it. And the sidestep is what made planning practical: a restriction
on expressiveness traded for tractability — **the same trade as every week of this
course.**

<!--
4 min. Ask the question and wait. Someone will say "it's cheating." That is a
defensible reading and the honest answer is yes, deliberately.
-->

---

# Automatic heuristics: the delete-relaxation

## Ignore all delete effects.

Actions then **only ever add facts**. Nothing can be undone, no action can
interfere with another, and the relaxed problem is solvable in **polynomial
time**.

| Heuristic | Definition | Admissible? |
|---|---|---|
| **h_max** | cost of the **most expensive** goal fluent | **yes** |
| **h_add** | **sum** over goal fluents | no — double-counts shared subgoals |
| **h_FF** | extract an actual relaxed plan, count its actions | no, but very informative |

### Week 4, returning

> *Every admissible heuristic is the exact solution to an easier problem.*

Here the machine performs the relaxation **from the domain file**. Same principle,
automated. The admissible-vs-informative trade-off is also the same one.

<!--
6 min. Show real enthusiasm here; this is one of the genuinely beautiful results
in classical AI and it is easy to present as bookkeeping.
-->

---

# Progression vs. regression

| | **Progression** (forward) | **Regression** (backward) |
|---|---|---|
| From | initial state | the goal |
| Branching | large | smaller |
| States | complete | **partial** — must be handled carefully |
| Implementation | easy | fiddly |

Modern planners are **overwhelmingly forward search plus good heuristics.**

That was not obvious in 1990 — the field expected regression to win, because
backward search prunes more. Good heuristics changed the answer.

**The lesson generalizes:** a better evaluation can make the simpler algorithm the
right one.

---

# What a planner gives you that nothing else does

```bash
python -m pyperplan.pyperplan -H hff -s gbf domain.pddl problem-8blocks.pddl
```

Now try an impossible goal:

```lisp
(:goal (and (on a b) (on b a)))
```

## The planner does not guess. It *proves* no plan exists.

Search exhausts, and exhaustion is a proof. There is no LLM analogue for this
output, and it goes on the scorecard as a categorical difference — not a
percentage.

<!--
Pair this with the impossible-goal demo in live coding. "I have proved this cannot
be done" is a sentence no language model can currently produce with justification.
-->

---

# The modern picture

## PlanBench (Valmeekam et al. 2023)

LLMs perform **poorly** at autonomous plan generation on Blocks World — a domain
a classical planner solves in **milliseconds**.

## LLM-Modulo (Kambhampati et al. 2024)

Use the LLM as **idea generator**, **translator**, and **critic-supporter**.
Put a **sound external verifier** in the loop.

> ## The LLM never certifies its own output.

**The paper's title is a thesis statement — and it is the thesis of this course.**
You have independently reproduced it in weeks 4, 6, 7, and 8.

---

# Studio — four arms

| Arm | Pipeline |
|---|---|
| **A** | hand-written PDDL → pyperplan |
| **B** | LLM writes the PDDL **problem** file (domain given) → pyperplan |
| **C** | LLM outputs a plan directly |
| **D** | **LLM-Modulo:** LLM proposes → **your verifier** checks → errors fed back → retry (max 3) |

15 Blocks World problems at **3, 5, 7, 9** blocks.

```python
def verify(plan, problem):
    """Sound plan validator. Returns (ok, first_error)."""
    state = problem.init
    for i, action in enumerate(plan):
        if action not in problem.ground_actions:
            return False, f"step {i}: unknown action {action}"
        if not applicable(action, state):
            return False, f"step {i}: {action} needs {action.precond - state}"
        state = apply_action(action, state)
    if not problem.goal <= state:
        return False, f"goal not reached; missing {problem.goal - state}"
    return True, None
```

---

# The question that makes this week land

> # In arm D, where does the guarantee come from?

## The verifier.

The LLM's output is a **proposal**. Correctness comes from a **sound checker**.

This generalizes far beyond planning:

> ## An unreliable generator plus a sound verifier can be a reliable system.

**That is how you build reliable systems out of unreliable components, and it is
the single most transferable idea in this course.**

It is also the answer to *"why learn this if LLMs exist."* Classical AI supplies
the verifiers.

<!--
Do not put this conclusion on the board before the studio. Let arm C's cliff and
arm D's recovery produce it, then push in the demos until a student states it
precisely. THEN write it on the board.
Expected shape: arm C degrades sharply with block count; arm D climbs back toward
arm A, because the verifier is sound.
-->

---

# One more practical lesson, guaranteed to happen

A pair omits a precondition. The planner returns a **valid** plan in which two
blocks are held in one hand.

> ## The planner is faithful to the model you wrote, not to the world you meant.

Name it out loud when it happens. It is the week's most important practical
lesson, and it is exactly the failure mode that makes arm B's translation errors
dangerous.

**Duel 2 (The Formalizer) is due this week.**
