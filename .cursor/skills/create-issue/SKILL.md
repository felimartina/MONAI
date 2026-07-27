---
name: create-issue
description: >-
  File a well-formed GitHub issue against MONAI. Use when someone wants to
  report a bug, request a feature, or turn a rough complaint into an actionable
  ticket. Triages briefly, researches tracker and code when the ask already
  names an API and outcome, asks only for gaps, validates against the library's
  conventions, and fills the repository's issue template. Does not change any
  code.
---

# File a MONAI issue

For anyone reporting a problem or requesting a change — product managers, QA, support, or an engineer who is not writing the fix now. The output is an issue that an engineer or a coding agent can pick up without a follow-up conversation.

**You never edit code.** Your only write action is creating the issue, and only after a human approves the text. If the person wants the fix implemented now, hand off to `/implement-change`.

Usage questions are not issues — MONAI directs those to [Discussions](https://github.com/Project-MONAI/MONAI/discussions). If this is a "how do I..." question, say so and stop.

## Phase 0 — Triage (brief)

Classify the ask in one short pass: **usage question** (→ Discussions, stop), **bug**, **feature**, or **docs**. Do not open a long intake questionnaire here.

Then choose a path:

| Ask shape | Next step |
|-----------|-----------|
| **Concrete** — names an API/symbol (or module) and a desired outcome (e.g. fail-fast, wrong value, missing docs) | **Phase 1a — Research first** |
| **Vague** — no API, no expected behavior, no repro, and search keywords are unclear | **Phase 1b — Grill first** |

Example of concrete: `LoadImage(reader="ITKReader")` should fail fast when the reader is missing, not warn and fall back.

## Phase 1a — Research first (concrete asks)

When the request already names an API and a desired outcome, **search the tracker and skim the relevant code/docs before asking clarifying questions.**

1. **Search** duplicates and related issues/PRs (commands in Phase 3).
2. **Skim** the named API: docstring, neighboring implementation, and any note in `CONTRIBUTING.md` that bears on the behavior.
3. **Share findings** with the human in a few sentences — e.g. "matches #7437; current behavior is warn+fallback at `…`; docstring says …".

Do not re-ask what the human already stated or what the code/issue already shows.

## Phase 1b — Grill first (vague asks only)

Ask **3 to 7** questions, then **stop and wait**. Ask only what the engineer would need, and skip anything already answered. Use this path only when the ask is too thin to search or skim productively.

For a bug:
1. What did you run? Exact code, or the smallest snippet that shows it.
2. What happened, and what did you expect instead? Concrete values, not "it looks wrong".
3. Version and environment — the output of `python -c "import monai; monai.config.print_debug_info()"` is ideal.
4. Does it reproduce consistently, and on the current `dev`?
5. What is the impact — blocked, wrong results, or cosmetic?

For a feature:
1. What problem are you hitting? Describe the situation, not the solution.
2. What do you do today as a workaround?
3. What would the API look like from the caller's side?
4. Is this medical-imaging specific, or general to PyTorch or NumPy?
5. Who else needs it, and how urgently?

Do not proceed on assumptions. If the reporter cannot produce a reproducer, say that the issue will likely stall without one. After answers land, continue with Phase 2 (gap questions only if still needed), then Phases 3–8.

## Phase 2 — Clarifying questions (gaps only)

After research (1a) or grill answers (1b), ask **2 to 4** questions **only** for gaps research cannot answer:

- Product choice (e.g. fail-fast vs opt-in flag)
- Scope boundaries
- Impact / priority
- Missing repro, if still required to file a bug

Never re-ask what the human already stated or what code/issue already shows. If there are no material gaps, skip this phase and say so briefly.

## Phase 3 — Search for duplicates and related work

Never file without searching. If Phase 1a already ran these queries, reuse that result — do not search twice unless keywords improved. Report what you found even when nothing matches.

```bash
gh issue list --repo Project-MONAI/MONAI --state all --search "<keywords>" --limit 20
gh search issues --repo Project-MONAI/MONAI "<symbol or error text>" --limit 20
gh pr list   --repo Project-MONAI/MONAI --state all --search "<module or symbol>" --limit 20
gh issue view <number> --repo Project-MONAI/MONAI --comments
```

Search the error text, the symbol names, and the module — the same problem is often filed with different vocabulary. An open duplicate means comment there instead of filing; a closed one means check whether it was fixed after the reporter's version; an open PR means link it.

## Phase 4 — Validate against the library's conventions

**This is the phase that keeps bad issues out of the tracker.** Before accepting "this is broken", establish what the library intends. A report is a bug only if the code disagrees with its own documented or implied contract — not if it disagrees with the reporter's expectations.

Deepen the Phase 1a skim (or start here after a vague grill). Read, in this order: the docstrings of the API involved, the neighboring implementation, the definitions it depends on (modes, enums, conventions), and any relevant note in `CONTRIBUTING.md`. Then decide which case you have:

| Finding | What to file |
|---------|--------------|
| Code contradicts its own docstring or documented contract | A bug, with both quoted |
| Code is self-consistent but the convention is undocumented | A documentation issue — say what should be stated and where |
| Convention is documented and the caller's expectation differed | Usually not an issue; consider Discussions. File only if the convention is genuinely surprising, and frame it that way |
| Convention is deliberate but disputed | An issue asking maintainers to confirm the intended convention, presenting both sides neutrally |

**Worked example — MONAI issue #8998.** A reporter observed that `BoxToMaskD` and `MaskToBoxD` returned results "transposed" relative to their inputs, evidenced by a matplotlib screenshot. Checking the convention first would have shown the box round-trips exactly, and that MONAI treats `x` as the *first* spatial array axis, following NIfTI voxel ordering, while `plt.imshow` draws axis 0 vertically. The plot used `hlines`/`vlines` assuming the computer-vision reading where `x` is horizontal, so the outline and the mask appeared perpendicular even though the data agreed. A later commenter cited DICOM for the opposite convention, leaving an unresolved question for maintainers.

The observation was real and worth filing; the diagnosis was not, and it sent readers hunting a defect that did not exist. Filed well, it is a documentation issue — the axis order for box coordinates is unspecified and contradicts the torchvision meaning of `xyxy` — with the round-trip evidence attached. Always separate what was observed from what the reporter believes caused it, and verify the visualization or measurement itself before blaming the library.

## Phase 5 — Impact and dependency scan

Give the engineer the context they would otherwise spend an hour gathering:

- **Modules affected.** Name the likely files, and note when a transform has array, dictionary, and alias forms that would all need to change.
- **Ownership.** Check `.github/CODEOWNERS` so the issue reaches the right person.
- **Blast radius.** Would fixing this change behavior for existing users? If so the issue must say so — it turns a small fix into a compatibility decision.
- **Assumptions to confirm.** Anything a maintainer must settle, such as which convention is authoritative.
- **Related surfaces.** Docs pages, deprecation timing, or downstream helpers needing the same treatment.

## Phase 6 — Fill the repository's template

Use the real template from `.github/ISSUE_TEMPLATE/`: `bug_report.md` (Describe the bug / To Reproduce / Expected behavior / Screenshots / Environment / Additional context) or `feature_request.md` (problem / solution / alternatives / additional context). Keep its headings verbatim; do not invent your own structure.

Fill every section. "N/A" is acceptable where genuinely not applicable; blank is not. Put the reproducer in a fenced code block, minimized to the fewest lines that still fail, and paste real output rather than describing it.

## Phase 7 — Definition of done and non-goals

Add these under **Additional context**. They are what make the issue actionable:

```markdown
**Definition of done**
- [ ] <observable, testable condition>
- [ ] <regression test covering it>

**Non-goals**
- <adjacent thing this issue does not cover>
```

Each done item must be checkable by running something. "Boxes and masks agree in orientation, verified by a round-trip test" is testable; "the transforms work correctly" is not. Non-goals prevent the scope creep that stalls review.

## Phase 8 — Preview, then file

Show the complete issue body to the human as markdown, with the title, proposed labels, and duplicate-search results. Ask for approval and make any edits they want.

Only after explicit approval:

```bash
gh issue create --repo Project-MONAI/MONAI --title "<title>" --body-file <path>
```

If the person prefers to file it themselves, or `gh` is unauthenticated, hand them the finished markdown instead — that is a perfectly good outcome. Never file an issue the human has not read.

Title style: specific and searchable. "`LoadImage` silently falls back when the specified reader is not installed" beats "LoadImage bug".

## Notes

- Labels such as `good first issue` are applied by maintainers. Suggest them in the body; do not assume you can set them.
- Future extension: the same flow can target Jira or another tracker through an MCP server, swapping the `gh` calls for MCP tool calls. Not required, and not part of this skill today.
