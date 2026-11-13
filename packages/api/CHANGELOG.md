# Changelog

Each version's changes that an application would notice. A breaking change is a new major version.

## Unreleased (0.2.0)

- `ai_app_platform.traceability` is new: `python -m ai_app_platform.traceability` checks that each requirement ID a specification's `Requirements:` line or a test cites is a requirement, that each test names the requirements it verifies, and that the committed trace report is current; `--write` regenerates the report. The `traceability-check` reusable workflow runs it.

## 0.1.1

- The package is marked as typed (`py.typed`), so type checkers such as Pyright read its types instead of reporting it as an untyped library.

## 0.1.0

The first release: the code the first application built, moved here unchanged (the standard's work plan, Feature F03.2).
