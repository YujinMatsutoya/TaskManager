---
name: test-planning
description: |
  Turn specs, tickets, stories or changes into a risk-prioritised, traceable test plan for the unit, integration, e2e and performance writer skills. Use for ANY request to plan tests, scope testing, list test cases or decide what to test, even if the user just says "what should we test for X". Do NOT use to write test code or run tests.
---

# Test planning

Phase 1 of planning → writing → execution → review. The writer skills build tests from your plan without re-reading the spec, so every expected result in it has to be traceable and defensible.

## Inputs
- **Read for behaviour:** specs, requirements, tickets, architecture docs, API/DB schemas, NFRs.
- **Read for inventory:** existing tests and coverage reports, so the plan doesn't duplicate what already exists.
- **Read for structure only:** source tree, module and component names, routes. Use it to name where a test attaches. Never read function bodies to decide what *should* happen: a plan copied from the code passes the bugs it was meant to catch.

## Workflow
1. **Check testability first.** For each requirement, ask whether it is specific, consistent and observable. Any that fail go in **Gaps** with a question for the spec owner, and get no test case. Don't invent a threshold, message or rule to fill the hole. A gap that's written down gets fixed; a guessed expectation becomes a test that enforces the guess.
2. **Derive cases** for each testable requirement: happy path, boundaries, invalid input, error paths, and state transitions.
3. **Assign exactly one level** per case: the cheapest one that can catch the failure.
   - `unit`: pure logic, validation, formatting
   - `integration`: real components together (API + DB, frontend + real backend)
   - `e2e`: a user journey that only works across the full stack. Keep these few, about one per critical journey; anything a lower level can catch goes there.
   - `performance`: only when an NFR states a threshold
4. **Prioritise by risk** (impact × likelihood): `P1` covers data loss, security, money, core journeys, and complex or recently changed areas. `P2` covers secondary flows and validation. `P3` covers cosmetic issues and rare edges.
5. **Add level-specific needs:**
   - **e2e:** list the UI contract the writer needs: routes, the elements involved and how to find them (role/label/test-id), and the visible states to assert. Any of these the spec doesn't define become a gap.
   - **performance:** you need a workload (users, request mix, data volume), thresholds that come from an NFR (e.g. p95 < 300 ms at 50 rps), and an environment. If no NFR gives a number, log a gap ("must be fast" is not a threshold) and write no performance case.
6. **Write the plan** in the format below. Save it to `test-plans/<slug>.md` unless the user names a path. Change nothing else.

## Plan format
~~~markdown
# Test plan: <feature>
Sources: <docs read, with versions/dates> · Revision: 1

## Cases
```yaml
- id: TP-001
  level: integration          # unit | integration | e2e | performance
  title: PATCH with empty body is rejected
  requirement_ref: Spec §PATCH /tasks/{id}, "empty body {} should be rejected (422)"
  preconditions: [a task exists]
  data_needs: [one task with all fields set]
  steps: [send PATCH {} to /tasks/{id}]
  expected: 422; the stored task is unchanged   # quoted or derived from the spec, never from code
  priority: P1
```

## Traceability
| Requirement | Cases | Status |      <!-- covered | gap | out of scope -->

## Gaps
| ID | Requirement (quoted) | Problem | Question for owner |   <!-- Problem: exactly one of vague | contradictory | unobservable | no NFR -->

## Out of scope
- <item>: <why, e.g. "story 2b says the reminder comes later">

## UI contract (e2e) · Performance setup (only if those levels appear)

## Change log
| Rev | Cases | Change | Decision | Source |   <!-- Decision: accepted | declined | n/a; one row per feedback item -->
~~~

## Revising from feedback
Later phases may send feedback: a case at the wrong level, a gap the writer found, a test that turned out flaky. When they do:
1. Find the cases it affects, and check the feedback against the spec rather than accepting it blindly.
2. Change only what the feedback justifies. A level change usually means rewriting the steps and data. A flaky case may need its preconditions or waits made explicit; flakiness on its own isn't a reason to drop a case.
3. Keep the IDs stable. Mark a removed case `status: withdrawn` instead of deleting it.
4. Bump the revision. Add one change-log row per feedback item, with the cases affected, the change, `accepted` or `declined` (give the reason when declining) and the source, and report the diff back.

## Anti-patterns
- An expected value with no `requirement_ref`, or one that only the code could have told you
- Pushing a check up to e2e because it "feels end-to-end" when an API call would catch the same failure
- Performance cases with made-up thresholds
- Leaving a requirement out of the traceability matrix, so nobody can tell whether it was covered, deferred or forgotten
