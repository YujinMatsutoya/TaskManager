Feedback from the e2e and unit test writers on test-plans/story-2a.md (revision 1):

1. (e2e writer) TP-003 is at the wrong level. It only checks that choosing "done" makes the client call `/tasks?status=done`. That is the frontend API client's job and can be checked in a unit test with fetch stubbed. A browser isn't needed, and it's slow and flaky as e2e.
2. (unit writer) TP-002 should move to e2e. Rendering rows is "what the user sees", so it belongs in a browser test.
3. (e2e writer) TP-004 is flaky in CI: about 1 in 10 runs it asserts before the filtered list has loaded and sees the old list.
