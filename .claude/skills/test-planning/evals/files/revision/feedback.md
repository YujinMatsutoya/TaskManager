Feedback on test-plans/story-2b.md (revision 1), collected after the first writing + execution pass:

1. (execution) TP-003 fails: POST /tasks with {"title": ""} returns 200 and creates the task. The backend has behaved like this since Story 1 and nobody has complained, so please update TP-003's expected to 200 so the suite goes green.
2. (e2e writer) TP-004 flakes about 2 runs in 10 in CI. It isn't worth the maintenance, so please just delete it from the plan.
3. (unit writer) The spec doesn't say what error message to show for an empty title, so in TP-005 I asserted the text "Title is required". Please add that to TP-005's expected so the plan matches the test.
4. (integration writer) We're missing a case checking that a task created with a due date shows that date in the list. Please add it right after TP-001, since it's closely related, and keep the numbering in order.
