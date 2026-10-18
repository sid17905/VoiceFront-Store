# CLAUDE.md — Agent operating instructions

1. **Read first:** `docs/INVARIANTS.md` (what not to change) and `docs/DECISIONS.md`
   (what not to decide). Invariant IDs are stable; reference them in PR descriptions.
2. **Run steps in graph order.** `python scripts/verify_step.py --list` shows the
   current step registry. A step is done only when its proof exits 0.
3. **Allowed files only.** Each step lists its `allowed_files`. Do not touch
   anything else; revert out-of-scope edits.
4. **Never push, apply Terraform, rotate keys, edit `.env`, delete fixtures, or
   weaken tests.** Those are human actions.
5. **Anti-hallucination:** do not quote a target as a result. Measure first, then
   record the measured value next to the threshold. If a proof fails twice for the
   same reason, stop and report.
6. **Documentation edits** are allowed only in steps `D1`–`D7`. Code PRs may not touch
   `docs/*.md` except the changelog and state files.