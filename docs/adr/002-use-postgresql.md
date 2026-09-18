# ADR-002: Use PostgreSQL as the System of Record

- Status: Accepted
- Date: 2026-09-18

## Context

The gateway needs persistent storage for:

- Clients
- API keys
- LLM request summaries
- Provider attempts
- Versioned pricing
- Audit logs

The system requires transactions, foreign keys, indexes, decimal values
and schema migrations.

## Decision

Use PostgreSQL as the system of record.

Use SQLAlchemy for persistence and Alembic for schema migrations.

PostgreSQL is classified as a critical dependency because API-key
authentication depends on it.

## Alternatives Considered

### SQLite

SQLite is simple for local development but provides a different
concurrency and operational model from the intended staging environment.

### MongoDB

MongoDB provides flexible documents but the gateway data has clear
relationships, transaction requirements and reporting queries that fit a
relational database.

## Consequences

### Positive

- Strong relational integrity
- Transaction support
- Foreign keys and check constraints
- Reliable `NUMERIC` support
- Powerful indexes and reporting queries
- Mature SQLAlchemy and Alembic integration

### Negative

- Requires connection-pool management
- Requires an additional service in local development
- Database unavailability makes the gateway not ready
- Schema changes require reviewed migrations