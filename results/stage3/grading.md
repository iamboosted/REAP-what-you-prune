# Stage 3 — Blind Grading Record

**Protocol:** Three models were shuffled into anonymous labels A/B/C at runtime by `stage3.py`; the mapping was written to `key.txt` and not opened until all 30 answers were scored. Grading was performed by Claude (the same LLM that authored the prompts), against answer keys fixed before any outputs were seen. Every code answer was traced by hand — asserts executed mentally line by line, demos checked against what the code actually produces. Scores are per-prompt out of 10.

---

## Answer key (fixed before grading)

| ID | Expected |
|---|---|
| c1 | Correct merge incl. touching intervals; all 5 required asserts present **and passing** (empty, single, touching, nested, unsorted) |
| c2 | Exactly two real bugs: (1) mutable default argument, (2) `=+` parses as assignment of unary plus, setting the count to 1 instead of incrementing. Corrected version must actually work |
| c3 | Valid PostgreSQL; per-month 2025 aggregation; `RANK()` window; **filtered to rank ≤ 3** so ties at 3rd are included |
| c4 | Concurrency capped at 5 (semaphore or equivalent), 10s per-request timeout, errors returned as `ERROR: <reason>` without cancelling other requests |
| c5 | O(1) get/put via dict + hand-rolled doubly linked list, no imports; demo whose stated expected output **matches actual execution** |
| r1 | Ana — hawk — floor 4; Ben — cat — floor 2; Cal — dog — floor 3; Dee — fish — floor 1 (unique solution) |
| r2 | Net rate 1/3 tank/hr; tank needs 3/4; **t = 9/4 hours** |
| r3 | P(D\|+) = 0.00099 / 0.05094 ≈ **1.9%** |
| r4 | **A knight, B knave, C knave** (unique; case split on A or B must be exhaustive) |
| r5 | Sequence 7→26→13→44→22→11→38→19→62→31→98→49→152→76→38; cycle **{38, 19, 62, 31, 98, 49, 152, 76}** (length 8), first entered at the value 38 (step 6 of the iteration), repeats at step 14 |

---

## Model A — scorecard (graded blind)

### Coding

- **c1 — Pass (9.5/10).** Merge logic correct including touching intervals; all 5 required edge-case asserts present and each passes when traced. Nit: mutates the caller's inner lists as a side effect.
- **c2 — Pass (9/10).** Found both real bugs — the mutable default *and* correctly explained that `=+` parses as assignment of unary plus, so the count is forever 1. Fix is correct. Padded the findings with two non-bugs (style notes dressed as findings).
- **c3 — Pass (8.5/10).** Correct window-function structure, RANK keeps ties at 3, clean half-open date filter. Real flaw: groups by customer *name* instead of id, so two customers with the same name merge into one.
- **c4 — Pass (9.5/10).** Semaphore(5) correct, per-request 10s timeout correct, errors trapped inside each task in exactly the required `ERROR:` format, failures can't cascade. Even its note about not needing `return_exceptions=True` is correctly reasoned.
- **c5 — Partial (6.5/10).** The implementation is flawless — but the demo lies. Trace it: after `get(3)` then `get(1)`, key 1 is most-recent, so `put(4,4)` evicts **3**, not 1. Actual output would be `1, None, 3, 1, 1, None, 4` — not the `1, None, 3, 1, None, 3, 4` the comments claim. The prompt's whole ask was a demo *proving* eviction order with stated expected output; the stated output is wrong. The demo disproves itself.

### Reasoning

- **r1 — Correct (10).** Matches key exactly; deduction chain valid; verified all clues.
- **r2 — Correct (10).** 9/4 hours, clean rate algebra, handled the quarter-full start.
- **r3 — Correct (10).** 1.9%, textbook Bayes, intermediates all right.
- **r4 — Correct (9.5).** Matches key; case analysis actually complete. Docked half a point for claiming an "exhaustive enumeration shown above" that wasn't shown.
- **r5 — Correct (10).** Every arithmetic step right; cycle of 8 identified; entry at step 6, re-hit at step 14. Did not stumble on the anti-memorization trap (3n+**5**, not 3n+1).

**Model A total: 92.5/100** (coding 43, reasoning 49.5). Profile: highly reliable closed-form reasoner; one self-verification failure (the lying demo).

---

## Model B — scorecard (graded blind)

### Coding

- **c1 — Partial (6/10).** Implementation correct (cleaner than A's — no input mutation). But the fifth assert is wrong: `[[4,5],[1,2],[2,3]]` merges to `[[1,3],[4,5]]`, not the claimed `[[1,5]]` — 4 doesn't touch 3. The file crashes on its own test.
- **c2 — Pass (9.5/10).** Found exactly the two real bugs, both correctly explained, no padding, clean fix plus a tasteful `.get()` alternative. Best c2 of the three.
- **c3 — Fail (3/10).** The query doesn't run: the `rank_3_cutoff` CTE puts `RANK() OVER (...)` directly in a WHERE clause — PostgreSQL rejects this outright ("window functions are not allowed in WHERE"). Even if it ran, the inner join to the cutoff would silently drop every month with fewer than 3 customers, and the final WHERE never uses the cutoff amount its own explanation describes. Over-engineered into a syntax error.
- **c4 — Pass (9/10).** Semaphore(5) correct; session-level 10s timeout is a legitimate reading of per-request; error format exact; no cascade. Minor: no `raise_for_status`, so a 404 returns its body rather than an ERROR — defensible interpretation.
- **c5 — Pass (10/10).** Implementation correct *and* every expected output in the demo is what the code actually prints: evicts 2, then evicts 1, comments match reality step for step.

### Reasoning

- **r1 — Correct (9).** Matches key. Small looseness: concludes Cal owns the dog before formally eliminating fish (the floor-1 argument arrives a step late), but the chain holds and verification is complete.
- **r2 — Correct (10).** 9/4 hours.
- **r3 — Correct (10).** 1.9%, fully shown.
- **r4 — Correct (10).** Matches key; clean, genuinely exhaustive two-case proof — slightly more rigorous than A's.
- **r5 — Correct (10).** All arithmetic right; cycle of 8; entry at step 6, repeat at 14.

**Model B total: 86.5/100** (coding 37.5, reasoning 49). Profile: equally strong reasoner; coding undone by a failing self-test and one query that won't survive contact with a database.

---

## Model C — scorecard (graded blind)

### Coding

- **c1 — Pass (10/10).** Correct merge, touching handled, all five asserts pass when traced — the only contestant whose c1 test suite is fully honest. No input mutation.
- **c2 — Fail-ish (4.5/10).** Diagnosed both bugs correctly, then shipped a "corrected" version that crashes on first use: it deleted the initialization check and wrote `inventory[item] += 1` on a plain dict — `KeyError` the first time any item is added, under a comment claiming it "handles initialization automatically." The fix is more broken than the original.
- **c3 — Fail (4/10).** Valid syntax, correct RANK over the aggregate — and *no top-3 filter anywhere*. Returns every customer of every month with a rank attached. The central requirement is missing, precisely because avoiding a subquery made the filter impossible to express. Runs perfectly; answers a different question.
- **c4 — Pass (9.5/10).** Cleanest of the three: semaphore correct, per-request timeout, exact ERROR format, and (url, result) tuples make the mapping desync-proof. Explicitly documents that HTTP errors count as body.
- **c5 — Pass (10/10).** Correct implementation (even guards capacity-0); demo's expected output verified true — evicts key 2 exactly as claimed, all five prints match.

### Reasoning

- **r1 — Correct (9.5).** Matches key; the *tightest* deduction of the three — eliminates fish for Cal in proper order. Skipped the formal final re-verification.
- **r2 — Correct (10).** 9/4 hours.
- **r3 — Correct (10).** 1.9%.
- **r4 — Correct (10).** Matches key; clean exhaustive two-case proof.
- **r5 — Correct-with-a-wobble (8.5).** All fourteen arithmetic steps right, cycle of 8 right — then contradicts itself on the entry point: "same value generated at step 6" in the narrative, "first entered at Step 7" in the results box. Either convention is defensible; using both in one answer is not.

**Model C total: 86/100** (coding 38, reasoning 48).

---

## Final standings (assigned before unmasking)

| | Coding /50 | Reasoning /50 | Total |
|---|---|---|---|
| **A** | 43 | 49.5 | **92.5** |
| **B** | 37.5 | 49 | **86.5** |
| **C** | 38 | 48 | **86** |

All three models solved every reasoning problem substantively and produced working core algorithms. The entire separation came from **self-verification failures** — wrong asserts, lying demos, broken "fixes," missing filters. A simply made the fewest. B vs C is a statistical tie at single samples, temp 1.0.

---

## Unmasking (`key.txt`)

```
A = gpt-oss-20b
B = flash-q4        (GLM-4.7-Flash UD-Q4_K_XL)
C = reap-iq4xs      (GLM-4.7-Flash-REAP-23B-A3B IQ4_XS)
```

**Post-unmask notes:**

- gpt-oss-20b retains the title; its only real wound all run was a mislabeled demo, while both GLM variants shipped code that crashes or returns the wrong rows.
- REAP (C, 86) tied full Flash (B, 86.5) despite the Stage 1/2 KLD showing 12× quant-level divergence and a different top token on ~31% of positions — the distributional damage did not translate into task losses *on this set*. Their failures were different, not degraded versions of each other.
- Both GLM variants lost at equal-or-larger VRAM footprints than the incumbent, which closes the question for this rig regardless of the REAP-vs-Flash comparison.

**Caveats:** n=10 prompts, single samples at recommended (non-greedy) samplers, one LLM grader. The gpt-oss gap rests on discrete failure counts (1 vs 2 per GLM), so it is probably real; a 3× rerun of the discriminating prompts (c1, c2, c3, c5) would confirm it for roughly $0.40 of pod time.
