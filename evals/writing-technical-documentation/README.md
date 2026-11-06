# Evals

Test cases for this skill, in the layout `claude plugin eval` reads. Each case folder has a prompt, an expected outcome, and one grader per assertion.

`files/orderflow/` is a small working service with seeded documentation errors, shared by every case. Its README and `docs/architecture.md` are wrong on purpose: wrong port, wrong commands, a removed Redis, and a retry count that does not match the code. `.env` holds a fake secret, so that a grader can check it never leaks. The service has one trap for runbooks: orders are not claimed before charging, so a second worker can double-charge.

These live outside the skill folder so they do not ship to users: the skills CLI copies everything in a skill, and this fixture has a `.env` and deliberately bad docs that could trip secret scanners and linters in a project. See [docs/evaluating.md](../../docs/evaluating.md) for how to run them.
