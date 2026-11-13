# Changelog

Each version's changes to the reusable workflows that an application would notice. A breaking change is a new major version.

## 0.1.0

The first release: the workflows the first application built, moved here unchanged apart from their header comments (the standard's work plan, Feature F03.3), with these differences from the first application's copies:

- `security-checks`: `lockfiles` is optional, and the dependency scan is skipped when it is empty.
- `web-checks`, `contract-check` and `build-application`: the `github-packages-scope` input reads that npm scope from GitHub Packages with the run's own token, so their jobs request `packages: read`, which the calling job grants.
- `workflow-checks` is new: actionlint, with shellcheck, from its image pinned by digest.
