# ADR-003: Use Redis for Caching and Rate Limiting

- Status: Accepted
- Date: 2026-09-18

## Context

The gateway needs:

- Low-latency response caching
- Expiring cache entries
- Per-API-key rate-limit counters
- Shared state if multiple API instances are introduced later

These values are temporary and do not need to be the primary system of
record.

## Decision

Use Redis for:

- Exact-match response caching
- Cache expiration through TTL
- Distributed per-API-key rate limiting

Redis is classified as a non-critical dependency.

When Redis is unavailable:

- Cache operations are bypassed
- Cache-read failures are treated as cache misses
- Rate limiting uses an in-memory fallback
- The gateway reports degraded readiness
- Chat traffic continues

## Alternatives Considered

### PostgreSQL

PostgreSQL could store counters and cached responses, but frequent
short-lived operations would add unnecessary database load.

### In-memory storage only

In-memory storage is simple but cannot share counters or cache entries
between multiple API instances.

## Consequences

### Positive

- Low-latency reads and writes
- Native TTL support
- Suitable for rate-limit counters
- Can support multiple API instances
- Reduces repeated provider calls

### Negative

- Adds another infrastructure dependency
- Cache data is not authoritative
- In-memory fallback is not globally accurate
- The application must implement graceful degradation
- Redis outages reduce cost protection and cache effectiveness