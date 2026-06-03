# Security

Grona is an early research prototype. It currently does not execute shell commands, spawn subprocesses, call external APIs, crawl the filesystem, or run real tools.

## Current Safety Boundary

The safety policy layer evaluates planned actions and returns deterministic policy decisions. It is a planning and explanation layer only.

It is not:

- a sandbox
- process isolation
- filesystem isolation
- a permission system
- a production security boundary
- a guarantee that future tool execution is safe

## Reporting Security Concerns

For now, please report security concerns through GitHub issues. Include:

- what behavior is concerning
- which command or code path is involved
- whether the issue is about current behavior or future tool-execution risk
- any minimal reproduction details

## Future Tool Execution

Any future real tool execution should be treated carefully. Before adding shell commands, subprocesses, filesystem access, network access, scanners, or external APIs, Grona needs explicit design for boundaries, user consent, audit logs, dry-run behavior, and failure handling.