# Production LLM Gateway

A production-oriented AI gateway that exposes a unified API for multiple
LLM providers while supporting authentication, routing, retry, fallback,
rate limiting, caching, usage tracking and observability.

## Project status

The project is currently in the requirements and system-design phase.

## Core capabilities

- Unified chat-completions API
- API-key authentication
- OpenAI and Gemini provider adapters
- Deterministic model routing
- Timeout, retry and provider fallback
- Redis caching and rate limiting
- PostgreSQL usage and cost tracking
- Structured logging and metrics
- Automated testing and CI
- Docker-based local environment

## Documentation

- [Product requirements](docs/requirements.md)
- [System architecture](docs/architecture.md)
- [API design](docs/api-design.md)
- [Database design](docs/database-design.md)
- [Implementation backlog](docs/backlog.md)
- [Architecture decisions](docs/adr/)

## MVP constraints

- Non-streaming responses
- Text input only
- No frontend
- No RAG or AI agents
- No Kubernetes
- Estimated cost is not an official billing source

## Development status

See [docs/backlog.md](docs/backlog.md) for the implementation roadmap.