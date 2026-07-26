---
name: implement-change
description: >-
  Golden path for making a change to MONAI: confirm the task, explore the
  codebase, plan, open a draft pull request, implement with tests, verify, and
  update the PR. Use for implementing a MONAI fix or feature, a first
  contribution to this repository, a change described by a GitHub issue, or any
  change that must follow MONAI's contribution conventions.
---

# Implement a MONAI change

This walks one change from a request to a pull request a maintainer can review. The expensive mistakes — no test, wrong layer, silent behavior change — all happen before anyone looks at the diff, so the ordering below matters more than the speed.

Repository conventions live in `AGENTS.md` and `.cursor/rules/`; this skill is the sequence, not a second style guide.

The task comes from the person invoking you: a description, or a GitHub issue number or URL. If you are given an issue, read it before anything else, including the comments:

```bash
gh issue view <number> --repo Project-MONAI/MONAI --comments
```

The thread is part of the request. Maintainer replies frequently narrow the scope, and sometimes dispute the premise.

## Phase 0 — Confirm the task

Do not open with a questionnaire. Read what you already have first: the request, the linked issue and its comments, and the code the issue names. Most of what a question would ask is already written down somewhere you have access to.

Then take the cheapest honest path.

**When the task is clear** — you can state the outcome, the scope, and the kind of change from the material in front of you — do not ask anything. Post a short reading and one request for confirmation:

```
Kind: bugfix
Outcome: <what is true afterwards, in API or user-visible terms>
Area: <module or file, if the material names it>
Compatibility: <non-breaking | opt-in | declared break>
Out of scope: <what you will not touch>

Correct me, or say go.
```

One message, one yes. Do not also ask a list of questions.

**When something genuinely blocks you**, ask at most **3** questions and stop. A question earns its place only if all three of these hold:

- the answer changes what you build, not just how you describe it
- you cannot get it from the issue, the code, or `git log`
- it is a decision only a human can make — intended behavior, tolerable breakage, scope boundary, priority

**Never ask:**

- what the code can tell you: which module, which test file, what the current behavior is. Read it, or let the explorer find it in Phase 1.
- open-ended framing questions when the issue already answers them. "What outcome do you want?" against a bug report with a repro is noise.
- anything stated in the request you were just handed.
- two questions about the same decision.

**If the person does not know, that is an answer.** Do not re-ask and do not stall. Name the assumption you are proceeding on, say why it is the safer default, and carry it into the PR description as an open question for the maintainer. A stated assumption a reviewer can correct beats a blocked task nobody in the room can unblock.

Questions that only become concrete after reading the code belong in Phase 2.

## Phase 1 — Explore

Launch the **`monai-explorer`** subagent with the request plus whatever Phase 0 settled. It is read-only and returns a one-page brief: target files, the pattern to follow, the test file to extend, exports and docs to touch, ownership risk, and open questions.

Read the brief before planning. If it names a canonical implementation, follow it rather than inventing a parallel approach.

## Phase 2 — Re-clarify (only if needed)

This is where a real question usually belongs, because now it is concrete and you can show the evidence behind it. Ask **1 or 2**, and only if the explorer surfaced something that changes the approach:

- the functionality already exists in MONAI
- the bug is at a different layer than assumed
- the path has a specialized owner in `.github/CODEOWNERS`
- the change would break existing users, so warn-versus-raise or opt-in-versus-default is a real decision
- documented behavior and actual behavior disagree, so "correct" is a judgment call

Otherwise proceed silently.

## Phase 2b — Reproduce first (bugfix only)

**Skip this phase only if the change is not a bugfix.** For a bugfix, do not write a fix before you have seen the failure.

1. Run the reporter's repro, or a minimal case built from the request. Capture the **actual** values and the exact command.
2. **Check the premise before accepting it.** A reported bug is sometimes a convention mismatch rather than a defect — a caller's assumption about axis order, coordinate convention, or defaults may differ from MONAI's. Confirm what the library intends from its docstrings, the neighboring code, and the definitions it relies on. If the code matches its own convention and only the documentation is silent, the fix is documentation: say so and stop rather than changing behavior.
3. If the failure is unclear, intermittent, or the mechanism is not obvious from reading, use Cursor's **Debug Mode**: state hypotheses, add instrumentation, gather evidence, then conclude.
4. Write a **failing regression test** in the file the explorer named. Run it and confirm it fails **for the reported reason**, not for a setup error.
5. Keep the captured before-state; it belongs in the PR's Verification section.

A "fix" with no reproduced failure is unreviewable. If you cannot reproduce it, say so and stop — that is a finding, and it changes the task.

## Phase 3 — Plan

Enter Plan Mode and produce a short plan in chat: the layer you will change and why, the files you will touch, the test cases you will add, and the compatibility call (non-breaking, opt-in, or declared break).

Keep it to something a reviewer could read in a minute. **Do not write the plan to a file** — its permanent home is the pull request description. Never create `docs/plans/*.md`.

## Phase 4 — Open the draft PR early

`CONTRIBUTING.md` asks for pull requests early, as drafts. Open it now, before implementing, so the plan is visible while the work happens.

1. Create the branch from **`cursor-onboarding`**, named `[ticket_id]-[task_name]` — e.g. `7980-writer-install-hint`. That is the integration branch in this repository. Branching from `dev` would put your work on a tree without this onboarding layer, so none of the rules, hooks, or skills would apply while you edit.
2. **Read `.github/pull_request_template.md`** and use it as the body's structure. It is the only PR template; never duplicate it under `.cursor/`.
3. Fill it from the plan:
   - `Fixes # .` → the issue number, or `N/A` plus one line on where the request came from
   - **Description** → the plan summary, in prose
   - **Types of changes** → check only what is already true; revisit after verification
4. Append one additive section at the end of the body — not a second template, not a scorecard:

```markdown
### Verification
- Commands run: (fill after local verify)
- Results: (paste key outcome)
- Agent pre-review (`monai-verifier`): (critical / nits)
- Bugbot: pending | clean | link
```

Open it as a draft against the branch you started from:

```bash
gh pr create --draft --base cursor-onboarding --title "..." --body "..."
```

Targeting `dev` instead would show this entire onboarding layer as part of your change. Contributing the same fix upstream to `Project-MONAI/MONAI` does target `dev`, and that is a separate step a human takes deliberately.

Do not add report-card matrices, self-assessment tables, or process narration. Reviewers want the change and the evidence.

## Phase 5 — Implement

- Follow the explorer's brief and the pattern it identified. Match the neighboring code's style, typing, and structure.
- Keep the diff minimal and scoped.
- The rules in `.cursor/rules/` apply as you edit, and the license and lint hooks run after each edit. Fix what they report rather than working around them.
- If a hook denies a write to a protected path, do not look for another route. Stop and tell the person which path the task appears to need.

## Phase 6 — Verify locally

Run the narrow thing first, and actually run it:

```bash
python -m tests.<path>.test_<module>   # the specific module you changed
./runtests.sh --ruff                   # fast lint
./runtests.sh --quick --unittests      # broader sweep when the change warrants it
```

For a bugfix, confirm the regression test now passes and that you can still explain why it failed before.

If the environment cannot run the tests, say exactly that and treat it as an open item — do not check the PR template's test boxes.

## Phase 7 — Agent pre-review

Launch the **`monai-verifier`** subagent. It is read-only and returns critical / should-fix / nit findings plus a ready-or-not verdict.

Fix everything in **Critical**. Address should-fix items or say why not, and re-run the affected tests afterwards. Do not argue with the verifier in chat — either fix the finding or record the reason in the PR.

## Phase 8 — Update the PR

- Refresh the Description if the approach changed during implementation.
- Update the **Types of changes** boxes so they are true now, including the breaking-change box.
- Fill **Verification** with the real commands and their key output, the verifier's summary, and Bugbot status.
- For a bugfix, include the before-and-after evidence from Phase 2b.
- Record any assumption you carried forward from Phase 0 as an open question for the reviewer.

## Phase 9 — Push and hand off

| Environment | Gate |
|-------------|------|
| IDE / local | Ask before committing or pushing when the intent is unclear; the human decides when the PR is ready |
| Cloud agent / automation | **Stop at the draft PR.** Never mark ready, never merge, never force-push |

Push and let Bugbot, CodeRabbit, and CI run. Mark the PR ready for review only when tests pass, the verifier has no criticals, and the human agrees.
