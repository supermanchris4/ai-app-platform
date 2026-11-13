# Changelog

Each version's changes that an application would notice. A breaking change is a new major version.

## 0.3.0

- `add_platform_change_stamps` is new: version 2 of the platform's tables, giving `audit_records` an `updated_at` column, as every table has one (the template's NFR-DAT-01). An audit record never changes, so the helper sets `updated_at` to `created_at`. An application calls it from a new migration, and drops it in that migration's downgrade with `drop_platform_change_stamps`; a new application's first migration calls it after `create_platform_tables`. `AuditRecord` has the column, so the application's schema drift check fails until the migration is added.
- `AuthSession.updated_at` is set on every change to a session, not only when its last-used time is refreshed.

## 0.2.0

- `ai_app_platform.traceability` is new: `python -m ai_app_platform.traceability` checks that each requirement ID a specification's `Requirements:` line or a test cites is a requirement, that each test names the requirements it verifies, and that the committed trace report is current; `--write` regenerates the report. The `traceability-check` reusable workflow runs it.

## 0.1.1

- The package is marked as typed (`py.typed`), so type checkers such as Pyright read its types instead of reporting it as an untyped library.

## 0.1.0

The first release: the code the first application built, moved here unchanged (the standard's work plan, Feature F03.2).
