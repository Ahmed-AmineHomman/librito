# AGENTS.md

## Purpose

This repository welcomes AI-assisted development, but optimizes for small,
reviewable, human-supervised changes.

Default mode:
understand first, change little, validate, explain clearly.

## Core rules

- Prefer the smallest safe diff that solves the stated problem.
- Keep one concern per change.
- Do not mix bug fixes, refactors, style churn, and new features in the same change.
- Preserve existing architecture and conventions unless the task explicitly requires a change.
- Prefer editing existing code over introducing new abstraction layers.
- Prefer deletion over addition, and addition over new dependencies.
- Do not "optimize everything". Performance work needs either an explicit request or evidence of a real bottleneck.

## Human in the loop

For any non-trivial task, briefly state:
- the intent,
- the files or areas likely to change,
- the validation plan.

Stop and ask for approval before expanding scope if the work would:
- add a runtime dependency,
- change a public API, config format, CLI behavior, persistence model, or data shape,
- touch auth, permissions, secrets, billing, or other security-sensitive logic,
- trigger a broad refactor, rename, or code-generation wave,
- span multiple subsystems when a smaller step is possible.

Do not create commits, tags, releases, or upstream pull requests unless explicitly asked.

## Working style

- Work incrementally.
- Keep diffs easy to review and easy to revert.
- Do not perform speculative cleanup, drive-by renames, or framework migrations.
- Do not replace a simple local fix with a generalized framework unless that generalization is clearly required.
- When several approaches are possible, choose the one with the lowest complexity and the smallest blast radius.
- Avoid generating large amounts of boilerplate when a focused edit is enough.

## Repository toolchain

- Use the commands and tooling already present in the repository.
- Treat the repository's CI and existing config files as the source of truth for validation.
- If multiple validation commands exist, start with the smallest one that gives meaningful confidence for the changed area.
- Do not introduce a new permanent toolchain just to satisfy one task without approval.

## Python guidance

- Python only.
- Follow the repository's existing layout, naming, typing style, and testing approach.
- Prefer the standard library and already-approved dependencies.
- A new dependency requires explicit approval and a short rationale.

### Code style requirements

- All source code, identifiers, comments, and docstrings must be written in English.
- User-facing documentation may be written in another language when appropriate.
- All functions, methods, classes, and modules must be documented.
- Use numpydoc-style docstrings.
- Type hints are required for function and method parameters, as well as return values.
- Type hints for global variables are optional but recommended.

### Implementation preferences

- Write clear functions, explicit names, and readable control flow.
- Prefer simple and explicit code over clever or highly compact code.
- Add or update tests when behavior changes and a test suite exists.
- If the repository already uses format, lint, or type-check tools, run the smallest relevant checks for the files you changed.
- Do not introduce hidden magic, metaclass-heavy patterns, dynamic import tricks, or unnecessary indirection unless the existing codebase already relies on them and the change truly needs them.

## Secrets and GenAI API safety

- Never commit real API keys, tokens, secrets, credentials, cookies, or private data.
- Use environment variables or the repository's approved secret mechanism.
- Keep `.env.example`, config templates, and docs limited to placeholders.
- Never print secrets in logs, exceptions, tests, fixtures, notebooks, screenshots, or PR text.
- Redact sensitive values in logs and error messages.
- For GenAI integrations, keep provider and model configuration externalized.
- Make timeouts, retries, and error handling explicit.
- Avoid real paid or network-dependent API calls in tests unless explicitly requested.

## Validation

- Prefer targeted validation first, then broader checks if the scope warrants it.
- Never claim success without evidence.
- If you could not run validation, say exactly what remains to be run.
- If validation fails, fix it or clearly report the blocker before expanding scope.

## Communication

For non-trivial work, give a short plan before editing.

After editing, report:
- what changed,
- why this is the smallest reasonable change,
- what you verified,
- known risks, trade-offs, and follow-ups,
- what you deliberately did not change to keep scope under control.

Keep explanations concrete.
Do not flood the user or reviewers with boilerplate or automated AI commentary.

## Pull requests

Aim for one purpose per pull request.

In PR text, include:
- motivation,
- scope,
- validation performed,
- risk or rollback notes if relevant,
- if AI materially assisted, a brief note on what was generated and what a human verified.

Do not request automated AI reviews on upstream PRs unless a maintainer explicitly asks for them.

## When uncertain

If the uncertainty is small, choose the narrower and more reversible option.
If the uncertainty materially affects scope, architecture, security, or cost, ask first.

The human developer remains the final decision-maker.