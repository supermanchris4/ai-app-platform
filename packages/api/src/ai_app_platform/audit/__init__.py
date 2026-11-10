"""Audit recording (specs/31-audit.md). Platform module: imports nothing of any application's.

Every application records its audit events through `AuditService`, naming its own entity types and
actions as strings; they are defined in the application, not here.
"""
