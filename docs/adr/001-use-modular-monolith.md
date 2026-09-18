# ADR-001: Use a Modular Monolith

- Status: Accepted
- Date: 2026-09-18

## Context

The Production LLM Gateway MVP will be implemented by one developer
within four weeks.

Authentication, caching, routing, provider fallback and usage tracking
participate in one request-processing flow. These capabilities do not
require independent deployment or scaling during the MVP.

The project still requires clear module boundaries and testability.

## Decision

Implement the backend as a modular monolith using FastAPI.

The application will be deployed as one unit while separating:

- API layer
- Application services
- Domain policies and interfaces
- Infrastructure adapters
- Database repositories
- Observability

Application services depend on interfaces rather than concrete provider
SDKs.

## Alternatives Considered

### Microservices

Each capability could be deployed independently.

This was not selected because it would add service discovery, network
failure modes, distributed tracing and deployment overhead without an
MVP requirement for independent scaling.

### Unstructured monolith

All logic could be implemented directly in route handlers.

This was not selected because it would create high coupling and make
unit testing difficult.

## Consequences

### Positive

- Lower operational complexity
- Easier local development
- Simpler deployment and debugging
- Clear transaction boundaries
- Modules can be unit tested
- Future extraction remains possible

### Negative

- Modules cannot scale independently
- One process failure affects the whole API
- Poorly enforced boundaries could create coupling
- Future extraction may require refactoring