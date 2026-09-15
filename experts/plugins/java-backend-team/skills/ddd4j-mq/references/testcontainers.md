# Testcontainers

> Collection date: 2026-09-11.

Tests must at least cover: container reachability, real publish/consume, headers, ack, nack/retry, duplicates, recovery, and close.

Prefer the official Testcontainers module; when none exists, use a bounded GenericContainer. When Docker is unavailable, mark BLOCKED/SKIPPED — not PASS.
