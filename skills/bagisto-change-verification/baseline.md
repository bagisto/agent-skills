# Establishing the baseline

Bagisto's suites do not start green on every checkout. Some tests assert
absolute counts (`meta.total`) that a seeded install does not satisfy, and the
suites share one database with no rollback between runs, so counts drift.

**Never report a failure count as a regression without comparing.** Revert your
change, run the same command, and diff the failing test **names** — not the
counts, which move on their own:

```bash
vendor/bin/pest <path> 2>&1 | grep -E "^  ⨯" | sed 's/ *[0-9.]*s *$//' | sort > /tmp/with.txt
# revert the change, re-run into /tmp/without.txt
comm -23 /tmp/with.txt /tmp/without.txt   # empty means you introduced nothing
```

An empty diff is the evidence that the gate passed. A count that went 3 → 4 is
not evidence of anything.
