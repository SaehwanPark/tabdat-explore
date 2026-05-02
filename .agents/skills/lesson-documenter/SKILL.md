---
name: lesson-documenter
description: Capture development friction, debugging lessons, setup traps, and project-specific gotchas in a durable lessons document so future contributors avoid repeating them.
---

# lesson-documenter

## Purpose

Use this skill when development reveals non-obvious friction that future agents or contributors should not have to rediscover.

Primary goals:

- Record practical lessons from setup, implementation, testing, debugging, and deployment.
- Preserve the cause, fix, and prevention advice.
- Keep lessons easy to scan and close to the project.
- Grow documentation structure only when the project needs it.

## What to Document

Document friction when it is likely to recur or is not obvious from code, tests, or standard tooling.

Good candidates:

- Setup steps that failed or required undocumented prerequisites.
- Dependency, environment, or version mismatches.
- Test failures with surprising causes.
- Debugging paths that looked plausible but were dead ends.
- Integration constraints between modules, services, or tools.
- Generated files, caches, migrations, or build artifacts that caused confusion.
- Domain assumptions that were discovered while implementing.

Do not document every routine mistake. Prefer lessons that would save meaningful future time.

## Where to Put Lessons

First inspect the repo for an existing convention, such as `LESSONS.md`, `docs/lessons.md`, `docs/development.md`, or contributor docs.

If no convention exists:

- For early-stage projects, create or update root `LESSONS.md`.
- For larger projects, use `docs/lessons.md` or a focused file under existing docs.
- Split into multiple lesson files only when a single file becomes hard to scan.

Follow the project's existing documentation style when possible.

## Lesson Format

Use concise entries that explain what happened and how to avoid it.

Recommended structure:

```markdown
## Short Lesson Title

- Context: What task or area exposed the issue.
- Symptom: What failed or was confusing.
- Cause: The underlying reason.
- Resolution: What fixed it.
- Prevention: What future contributors should do first.
```

If the lesson is small, combine fields into a short paragraph and keep the prevention step explicit.

## Workflow

When friction occurs:

1. Finish enough investigation to know the actual cause.
2. Check whether the lesson is already documented.
3. Add or update the smallest useful entry.
4. Link to relevant files, commands, or docs when that reduces ambiguity.
5. Keep the lesson factual; avoid blame or diary-style narration.

Before finalizing work, mention any lesson document updates in the final response.
