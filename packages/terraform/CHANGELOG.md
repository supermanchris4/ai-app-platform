# Changelog

Each version's changes that an application would notice. A breaking change is a new major version.

## 0.1.0

The first release: the modules the first application built, moved here unchanged apart from their documentation (the standard's work plan, Feature F03.3), with these changes:

- `rds-postgres`: `deletion_protection` defaults to `true`, so an instance is protected unless the application turns it off. Applications that set it are unaffected.
- `cdn-distribution`: the viewer security policy is the new input `minimum_tls_policy`, used when `certificate_arn` is set. It defaults to `TLSv1.2_2021`, as before, and also accepts `TLSv1.2_2025` and `TLSv1.3_2025` (TLS 1.3 only), which need an AWS provider that knows them (6.73 does).
- `internal-load-balancer`: the HTTPS listener uses `ELBSecurityPolicy-TLS13-1-2-Res-PQ-2025-09`, AWS's recommended policy, instead of `ELBSecurityPolicy-TLS13-1-2-2021-06`. It drops TLS 1.2's CBC ciphers and adds quantum-safe key exchange for TLS 1.3. CloudFront still connects, over TLS 1.2 with ECDHE and AES-GCM. A plan shows the listener updated in place.
- `rds-postgres`: the parameter group sets `ssl_min_protocol_version` to `TLSv1.2`, so the minimum no longer depends on RDS's default. A plan shows the parameter group updated in place; the instance applies it without a restart.
