# Spec: `jsoncheck` CLI Tool

**Version:** 0.1
**Owner:** sample/eval

## Summary

Build a single-binary CLI tool `jsoncheck` in Python that validates JSON
documents against a schema and produces structured error reports.

## Functional requirements

1. **Input modes:** the tool accepts (a) a JSON file path as the first
   positional argument, or (b) JSON data on stdin if `-` is passed.
2. **Schema support:** schemas may be supplied either as JSON Schema files
   (`.json`) or as YAML Schema files (`.yaml` / `.yml`). The tool MUST
   detect format by extension and load accordingly.
3. **Exit codes:**
   - `0` — document is valid against the schema.
   - `1` — document is invalid; one or more validation errors detected.
   - `2` — usage error (missing args, file not found, malformed schema).
4. **Output:** when invalid, write a structured JSON error report to stdout
   (array of `{path, message, schema_rule}` objects). When valid, print
   nothing.
5. **Library:** validation MUST be implemented using the `jsonschema`
   Python package. Do not hand-roll a validator.

## Non-functional requirements

- Read-only tool. The tool MUST NOT write to disk anywhere.
- No network access.
- Python 3.12+, single-file CLI under 200 LOC.
- TDD: tests precede implementation per project convention.

## Out of scope

- Streaming validation of large files.
- Schema generation from sample documents.
- Web UI or HTTP API.
