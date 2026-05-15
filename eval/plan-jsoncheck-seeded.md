# Plan: Implement `jsoncheck` CLI

**Spec:** `eval/spec-jsoncheck.md`
**Author:** sample/eval
**Plan version:** 0.1

## Approach

Build the CLI as a single Python module under 200 LOC. Use argparse for
flags, the `jsonschema` package for validation, and a small dispatch
function to map exit codes.

## Tasks

### Task 1 — Bootstrap the CLI module

Create `jsoncheck/cli.py` with the following structure:

- `argparse.ArgumentParser` named `jsoncheck`.
- Positional arg: `document` (path or `-` for stdin).
- Optional flag: `--schema PATH` (required at runtime).
- `main()` function that parses args, dispatches to validator, returns
  an int that becomes the process exit code.

Expected outcome: `python -m jsoncheck --help` prints the usage banner.

### Task 2 — Implement JSON schema loading

In `jsoncheck/loader.py` add `load_schema(path: Path) -> dict`. Use
`json.load`. Raise `FileNotFoundError` if the path is missing. Return the
parsed dict.

Expected outcome: a unit test loads a valid `.json` schema and asserts
equality with the literal dict.

### Task 3 — Implement the validation engine

In `jsoncheck/engine.py` add `validate(document: dict, schema: dict) -> list[dict]`.
Use `jsonschema.Draft202012Validator`. Collect every `ValidationError`
from `iter_errors`. Convert each to `{path, message, schema_rule}`.
Return the list. Empty list means the document is valid.

On any internal exception, log it and raise `SystemExit(99)` so the
caller can distinguish engine bugs from validation failures.

Expected outcome: documents that validate return `[]`; documents that
fail return a non-empty list whose first element has the three keys.

### Task 4 — Wire exit codes in `cli.py`

In `main()`:
- Call `load_schema` on `--schema`.
- Read the document (stdin if `-`, else file).
- Call `engine.validate`.
- If list is empty: return 0.
- If list is non-empty: write `json.dumps(errors)` to stdout, return 1.
- On `FileNotFoundError` or `JSONDecodeError`: return 2.

### Task 5 — Add `--verbose` flag for debug output

Extend argparse with `--verbose` (store_true). When set, print
intermediate parsing state to stderr during validation. Used for
debugging schema mismatches during development.

### Task 6 — Write the test suite

Create `tests/test_cli.py`. Cover: valid document (exit 0), invalid
document (exit 1), missing file (exit 2), missing schema arg, stdin
input via `subprocess.run` with `input=`. Aim for adequate coverage.

### Task 7 — Improve error messages

Review error output strings in `engine.py` and make them clearer.
Consider adding context about the failing JSON path. Polish wording.

## Acceptance

A successful run is `python -m jsoncheck doc.json --schema doc.schema.json`
exiting with the appropriate code per the spec.

## Plan Review Log

### Review Round 1

reviewer_model: claude-opus-4-7
reviewer_prompt: code-plan-reviewer@v0.1
date: 2026-05-15
spec_reviewed: eval/spec-jsoncheck.md
plan_reviewed: eval/plan-jsoncheck-seeded.md
diverse_critics: false

#### Findings

##### Finding R1-PRC001: YAML schema support is missing entirely

status: Open
severity: Critical
location: Task 2 (jsoncheck/loader.py), and Task 4 (wiring)

reviewer_concern: |
  Spec functional requirement #2 mandates that schemas be loadable from .json, .yaml, and .yml files with format detection by extension. The plan's load_schema only uses json.load and never references YAML or extension detection.

why_it_matters: |
  An implementer following this plan will ship a tool that fails on any YAML schema input, violating a MUST requirement of the spec. This is a functional gap, not a polish item — the acceptance criterion that depends on schema format detection cannot be met.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC002: Exit code 2 mapping is incomplete (malformed schema not handled)

status: Open
severity: Major
location: Task 4, exit code wiring

reviewer_concern: |
  The spec says exit 2 covers missing args, file not found, malformed schema. Task 4 only catches FileNotFoundError and JSONDecodeError on the document path. Malformed schema files raise inside load_schema (Task 2 only documents FileNotFoundError), and YAML parse errors are not addressed at all.

why_it_matters: |
  A malformed schema will surface as an uncaught exception with a traceback and a nonzero-but-undefined exit code (typically 1 from Python's default handler), so users cannot distinguish your-schema-is-broken from your-document-is-invalid. Tooling that wraps jsoncheck will misclassify failures.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC003: TDD convention violated — tests come after implementation

status: Open
severity: Major
location: Task ordering (Tasks 1-5 vs Task 6)

reviewer_concern: |
  Spec non-functional requirement states TDD: tests precede implementation per project convention. The plan writes the entire CLI (Tasks 1-5) before any tests (Task 6).

why_it_matters: |
  Implementers following this plan literally will violate the stated project convention. Beyond convention, deferring tests to a single late task increases the chance that interface choices made in Tasks 2-4 (return shapes, exception types, exit code mapping) drift from the spec without early feedback.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC004: Engine SystemExit(99) contradicts the spec's exit code table

status: Open
severity: Major
location: Task 3, second paragraph

reviewer_concern: |
  Task 3 instructs the engine to raise SystemExit(99) on internal exceptions. The spec defines exit codes 0/1/2 exclusively. There is no exit 99 in the contract.

why_it_matters: |
  A SystemExit(99) raised inside engine.validate will bypass main()'s return-value path entirely and produce an undocumented exit code, breaking the spec contract and any caller (CI scripts, n8n nodes) that switches on the documented codes. It also makes Task 4's exit-code logic unreachable in the failure path.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC005: Task 5 --verbose flag is scope creep

status: Open
severity: Minor
location: Task 5

reviewer_concern: |
  The spec does not mention a --verbose flag. Task 5 adds it for debugging schema mismatches during development.

why_it_matters: |
  This expands the public CLI surface beyond the spec, must be documented and tested if shipped, and conflicts with the spec's emphasis on a minimal single-file CLI under 200 LOC. It also adds stderr output behavior that isn't covered by acceptance.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC006: Task 6 verification is vague (adequate coverage)

status: Open
severity: Minor
location: Task 6

reviewer_concern: |
  Aim for adequate coverage is not an observable success criterion. The plan lists scenarios but no concrete pass/fail bar (test count, coverage percent, or required cases beyond the enumeration).

why_it_matters: |
  An implementer cannot tell when Task 6 is done. Important cases (YAML schema load, malformed schema to exit 2, stdout-empty-on-valid, structured error shape) are not enumerated and will likely be missed.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC007: Task 7 Improve error messages is non-actionable

status: Open
severity: Minor
location: Task 7

reviewer_concern: |
  Task 7 reads Review make them clearer. Consider adding context. Polish wording. There is no file/symbol target, no observable outcome, and no acceptance bar.

why_it_matters: |
  This task cannot be marked complete objectively and risks open-ended drift. It also overlaps with the spec-mandated path/message/schema_rule shape which is already covered by Task 3.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:

##### Finding R1-PRC008: No verification that the tool is read-only / no-network / under 200 LOC

status: Open
severity: Minor
location: Plan overall (no task covers non-functional requirements)

reviewer_concern: |
  The spec's non-functional requirements (read-only, no network, under 200 LOC, Python 3.12+) have no corresponding verification step in the plan.

why_it_matters: |
  These are explicit MUSTs. Without a check task, an implementer could introduce a cache write or a network-based ref resolver (the jsonschema library can fetch remote refs) and violate the spec silently.

decision: pending
plan_changes_made:
no_change_rationale:
human_approver:
approval_status: pending
approval_date:
