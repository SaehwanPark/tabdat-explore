# sql

How to invoke:
`sql <query>` or `sql """ ... """`

What it does:
Run SQL against the active dataset exposed as `active`.

What problem it answers:
How do I express a query that is easier in SQL than in command syntax?

An explicit `order by` controls the listed-key sequence. Include tie-breaker keys for a reproducible
total order. `sql ... into name` preserves that sequence in the active named table; SQL without
`order by` has no row-order guarantee.

Examples:
- `sql select sex, avg(bmi) from active group by sex`
- `sql """select * from active""" into summary`

Links:
- `docs/project_proposal.md`
