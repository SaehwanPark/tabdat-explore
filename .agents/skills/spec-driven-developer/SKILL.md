---
name: spec-driven-developer
description: Maintain SPEC.md, ARCHITECTURE.md, and CHANGELOG.md while implementing features so project intent, current design, and release history stay accurate.
---

# spen-driven-developer

## Purpose

Use this skill when implementing, reviewing, or planning code changes in a repo that should keep root project documents aligned with development.

Primary goals:

- Treat `SPEC.md` as the source of feature state.
- Keep `ARCHITECTURE.md` accurate enough for new contributors.
- Update `CHANGELOG.md` at meaningful checkpoints.
- Leave future agents with clear project intent and current design context.

## Required Project Files

At the repo root, manage these files when they exist or when the project expects this workflow:

- `SPEC.md`: feature inventory split into past, present, and future.
- `ARCHITECTURE.md`: high-level structure, module responsibilities, and process or data flow.
- `CHANGELOG.md`: notable completed changes, grouped by checkpoint or release.

If a required file is missing and the task involves feature work, create the minimum useful version unless the user or repo has a different documentation convention.

## SPEC.md Workflow

`SPEC.md` should have three clear categories:

- Past: features already implemented.
- Present: features being implemented or actively in progress.
- Future: planned features or work that should be done later.

Before implementing a feature:

1. Read `SPEC.md`.
2. If the feature appears in Future, move or copy it into Present and mark the work as active.
3. If the feature is not listed, add a concise Present item describing the feature and expected outcome.
4. Preserve unrelated feature entries and wording.

After implementing the feature:

1. Update the Present item with the actual result.
2. Move completed work into Past.
3. Leave incomplete follow-up work in Present or Future, depending on whether it is actively underway.
4. Make sure the feature state in `SPEC.md` matches the code, tests, and docs.

## ARCHITECTURE.md Workflow

Update `ARCHITECTURE.md` whenever a change affects project structure, module boundaries, major dependencies, control flow, data flow, storage, APIs, or operational behavior.

The document should help a new contributor quickly answer:

- What are the main modules or services?
- What does each major part own?
- How does data or control move through the system?
- Which files or directories are the likely entry points?
- What invariants or boundaries should future changes preserve?

Keep the document high level. Prefer diagrams in plain text or short ordered flows when they clarify the design.

## CHANGELOG.md Workflow

Update `CHANGELOG.md` at important checkpoints, including completed features, meaningful behavior changes, migrations, compatibility changes, and fixes worth calling out.

When the changelog is stale:

1. Read `SPEC.md` and recent project changes.
2. Identify completed features not yet reflected in `CHANGELOG.md`.
3. Summarize them in user-facing language.
4. Avoid listing noisy internal edits unless they affect users, operators, or contributors.

If the repo does not define a changelog style, use a simple reverse-chronological structure with an `Unreleased` section.

## Final Check

Before finishing work:

- Confirm `SPEC.md` has the correct past, present, and future state.
- Confirm `ARCHITECTURE.md` reflects any structural or flow changes.
- Confirm `CHANGELOG.md` includes important completed checkpoints.
- Mention any documentation updates in the final response.
