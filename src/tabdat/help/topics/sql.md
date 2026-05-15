# sql

How to invoke:
`sql <query>` or `sql """ ... """`

What it does:
Run SQL against the active dataset exposed as `active`.

What problem it answers:
How do I express a query that is easier in SQL than in command syntax?

Examples:
- `sql select sex, avg(bmi) from active group by sex`
- `sql """select * from active""" into summary`

Links:
- `docs/project_proposal.md`
