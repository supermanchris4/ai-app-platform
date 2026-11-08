# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

The shared platform code for applications built from the AI application template (`ai-app-template`), following the AI application standard (`ai-app-standard`), released as versioned packages (see `README.md`). The work is planned in the standard's work plan, Epic E03, and tracked in its `work/tracker.md`.

The template's specifications are the source of truth for what each package does. Each package says which specifications it implements; its tests show they are met.

## Rules

- **No application code.** No package imports, names or assumes any application's code, domain, roles, entity types or people. What differs between applications is an input: settings, configuration files, or arguments.
- **Versions are promises.** A change an application would notice (an import path, a setting, a function's behaviour, a table) is noted for the package's next release, and a breaking one is a new major version.
- Changes reach `main` only through pull requests whose checks pass. Claude does not push to `main`, and runs `git push` only when the user asks.

## Stop rules

Stop and report to the user, without continuing the task, when any of these happen:

- **A credential is found** in a file, a log, command output or a commit. Report the file path and the type of credential. Never repeat, copy, move or use the value.
- **A secret is about to be written to a file.** This repository is public. Secrets never go in code, tests, fixtures, examples or pipeline variables; test keys are generated when the tests run.
- **Real data is about to enter the repository.** Only synthetic data, such as obviously made-up people, is held here.
- **Code is about to be written outside the WSL Linux filesystem** (a path such as `C:\` or `/mnt/c/`).
- **A change would deploy or alter cloud resources.** Claude does not run `terraform apply`, `terraform destroy` or AWS CLI commands.

## Hardening

Workflows follow the template's `13-delivery-pipeline.md`: actions pinned to commit SHAs with the version in a comment, scanners run from images pinned by digest, `permissions: {}` at the top and only what each job needs, no `pull_request_target`, checkouts without the token, and Dependabot with a 7-day cooldown.
