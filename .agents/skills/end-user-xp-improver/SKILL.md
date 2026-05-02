---
name: end-user-xp-improver
description: Improve product and interface decisions by identifying target end users, use cases, pain points, and friction-reducing defaults before adding or changing features.
---

# end-user-xp-improver

## Purpose

Use this skill when designing, implementing, reviewing, or documenting features that affect how real users understand, operate, or benefit from a project.

Primary goals:

- Make the intended users and usage contexts explicit.
- Optimize workflows around likely user pain points.
- Prefer frictionless defaults and clear recovery paths.
- Keep product-facing documentation understandable to future contributors and users.

## Discover the User Context

Before changing user-facing behavior:

1. Read the README and relevant docs for stated audience, use cases, and operating context.
2. Inspect existing UI, CLI, API, examples, or tests to infer how users currently interact with the project.
3. Identify the likely end-user groups if they are not explicitly documented.
4. Note the main job-to-be-done, where the project is used, and what success looks like for those users.

If the audience or use cases are missing or ambiguous, update the appropriate project documentation with a concise statement of:

- Who the project is for.
- When or where they use it.
- What problem it helps them solve.

## Design for Low Friction

When adding or changing a feature, make the best practical guess about user pain points and reduce them.

Prefer:

- Clear defaults that work for common cases.
- Minimal required setup before first value.
- Helpful validation errors with next-step guidance.
- Interfaces that match existing project conventions.
- Progressive disclosure for advanced options.
- Stable, predictable behavior over surprising automation.
- Accessible labels, states, and feedback for UI changes.

Avoid:

- Requiring users to understand internals before using the feature.
- Adding configuration without a clear reason.
- Silent failures or vague error messages.
- Workflow dead ends.
- Documentation that only describes implementation details.

## Documentation Expectations

When user groups or use cases were inferred, document them as assumptions unless the project already establishes them.

Good places to update:

- README overview or usage section.
- Product or feature docs.
- CLI help text or examples.
- API docs for user-facing contracts.
- Onboarding or getting-started docs.

Do not create new documentation files when an existing doc is the obvious home.

## Review Checklist

Before finalizing a user-facing change:

- Can the target user understand what to do next?
- Does the common path require the fewest reasonable decisions?
- Are errors actionable?
- Are advanced controls optional or clearly separated?
- Is the audience or use case documented if it was previously unclear?
- Did the change preserve existing workflows unless intentionally changed?
