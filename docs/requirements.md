# Production LLM Gateway — Product Requirements

## 1. Document information

- Status: Approved for MVP
- Ticket: AI-101
- Project duration: Four weeks
- Target: Portfolio-grade production AI service
- Last updated: 2026-09-17

## 2. Problem statement

Internal applications are integrating directly with different LLM
providers. This distributes credentials across applications, duplicates
retry and fallback logic, and makes usage, cost and reliability difficult
to monitor.

The company needs a centralized LLM gateway that provides a unified API
for accessing multiple providers while managing authentication,
reliability, caching, rate limiting and usage tracking.

## 3. Product goals

The MVP shall:

1. Provide one API contract for multiple LLM providers.
2. Centralize provider credentials and API-key authentication.
3. Continue serving requests when one provider temporarily fails.
4. Control traffic and LLM cost.
5. Track provider usage, latency and estimated cost.
6. Provide sufficient logs and metrics for troubleshooting.
7. Run locally through Docker Compose.
8. Be automatically tested through CI.

## 4. Target users

### Application developer

Uses the gateway to access LLM providers through one API.

### Platform administrator

Creates and revokes client API keys and controls configuration.

### Engineering operator

Monitors traffic, errors, latency, provider health and estimated cost.

## 5. Scope

### 5.1 In scope

- FastAPI backend
- `POST /v1/chat/completions`
- Non-streaming text responses
- Request validation
- Standard error responses
- API-key authentication
- OpenAI and Gemini adapters
- Configurable primary and fallback providers
- Deterministic model routing
- Timeout, retry and fallback
- Redis rate limiting
- Exact-match response caching
- PostgreSQL usage tracking
- Estimated cost calculation
- Health endpoints
- Structured logging and metrics
- Unit, integration and E2E tests
- Docker Compose
- GitHub Actions
- Load and failure testing
- Technical documentation and runbook

### 5.2 Out of scope

- Streaming responses
- Web or mobile frontend
- RAG and vector databases
- AI agents and tool calling
- Image, audio or video input
- Model training or fine-tuning
- Semantic caching
- LLM-based routing
- JWT authentication
- Full RBAC
- Admin dashboard
- Official billing
- Kubernetes
- Multi-region deployment
- Production compliance certification
- Background workers
- Automatic daily usage summaries

## 6. Functional requirements

### FR-01 — Unified chat API

The system shall provide `POST /v1/chat/completions` for non-streaming
text-generation requests.

A successful response shall contain:

- `request_id`
- `provider`
- `model`
- generated content
- usage metadata
- cache metadata
- fallback metadata

### FR-02 — Request validation

The system shall validate the request before invoking a provider.

Invalid requests shall return HTTP 422, and no provider shall be called.

Requests with `stream=true` shall return HTTP 422 with error code
`STREAMING_NOT_SUPPORTED`.

### FR-03 — API-key authentication

The chat API shall require a valid and active API key.

Missing, invalid or revoked keys shall return HTTP 401. Provider calls
shall not occur when authentication fails.

Only a secure key digest and identifiable prefix shall be stored. The raw
key shall be displayed only once when created.

### FR-04 — Provider abstraction

OpenAI and Gemini shall be accessed through a common provider interface.

Provider-specific SDK behavior shall not be exposed to the service layer
or client.

### FR-05 — Model routing

When the request specifies `model: "auto"`, the system shall choose a model
using deterministic routing rules.

Primary and fallback providers shall be externally configurable rather
than hard-coded into business logic.

### FR-06 — Timeout and retry

Each provider attempt shall have a default timeout of 10 seconds.

The primary provider may be retried once for eligible transient failures.
Retry shall use bounded exponential backoff.

The entire request shall have a maximum deadline of 25 seconds.

Authentication errors, invalid requests and unsupported models shall not
be retried.

### FR-07 — Provider fallback

If the primary provider remains unavailable after an eligible retry, the
system shall attempt the configured fallback provider.

Successful fallback shall return HTTP 200 and record
`fallback_used=true`.

If all providers fail, the API shall return HTTP 503 with error code
`LLM_PROVIDER_UNAVAILABLE`.

### FR-08 — Rate limiting

Each API key shall be limited to 30 requests in a 60-second window.

Requests above the limit shall return HTTP 429 with error code
`RATE_LIMIT_EXCEEDED` and a `Retry-After` header.

### FR-09 — Response caching

Caching shall occur only when:

- the client sends `cache=true`;
- server-side policy allows caching;
- the request is not marked sensitive;
- the provider response is successful.

The default cache TTL shall be 600 seconds.

The cache key shall include the API-key identity, model, messages,
temperature and system-prompt version. The canonical cache-key input
shall be hashed before storage.

Cache entries shall be private to an API key in the MVP.

### FR-10 — Redis degradation

If Redis is unavailable:

- the chat API shall remain available;
- response caching shall be bypassed;
- rate limiting shall use a temporary in-memory fallback;
- the failure shall be recorded through logs and metrics.

### FR-11 — Usage tracking

Each API request shall create a request record containing:

- request ID
- API-key ID
- provider and model
- status and error code
- input and output tokens
- provider latency
- retry count
- fallback status
- cache status
- estimated cost
- creation timestamp

Raw API keys, prompts and complete responses shall not be stored by
default.

### FR-12 — Cache-hit accounting

A cache hit shall still create a request record.

For a cache hit:

- source shall be `cache`;
- provider-call count shall be zero;
- newly consumed provider tokens shall be zero;
- additional provider cost shall be zero.

### FR-13 — Cost calculation

Estimated cost shall be calculated using provider-reported token usage
and the configured model-pricing table.

If token usage is unavailable, estimated cost shall be marked unavailable.
Provider billing remains the final source of truth.

### FR-14 — Usage persistence failure

If generation succeeds but saving usage fails, the API shall return the
generated result to the client.

The persistence failure shall be recorded through logs and metrics.

### FR-15 — Health endpoints

The system shall provide:

- `GET /health/live`
- `GET /health/ready`

Redis failure shall produce HTTP 200 with status `degraded`.

Failure of a critical dependency such as PostgreSQL shall produce HTTP
503 with status `not_ready`.

Health responses shall not expose credentials or connection strings.

### FR-16 — API-key management

The MVP shall provide a CLI command for creating API keys.

The raw key shall be displayed once. Revocation shall be supported through
a CLI command or database-backed administrative command.

### FR-17 — Data retention

Usage metadata shall have a retention target of 90 days.

The MVP shall provide a manual cleanup command. Automatic scheduled
cleanup belongs to the roadmap.

## 7. Non-functional requirements

### NFR-01 — Security

Secrets shall be supplied through environment variables and shall not be
committed to Git.

Logs shall not contain raw API keys, provider credentials, database
passwords or full prompts and responses.

### NFR-02 — Reliability

Provider failures shall not crash the API process.

Retries shall be bounded, and fallback shall not create an infinite loop.

### NFR-03 — Graceful degradation

Failure of a non-critical dependency shall reduce optional functionality
without stopping the core chat API.

### NFR-04 — Performance

Internal p95 processing latency shall remain below 300 ms during the
defined 30-concurrent-user load test, excluding provider generation time.

### NFR-05 — Observability

Every request shall use the same `request_id` across:

- API response
- structured logs
- usage record
- provider attempts
- metrics or traces where supported

### NFR-06 — Testing

Model routing, cost calculation, retry policy, fallback policy and rate
limiting shall have unit tests.

PostgreSQL and Redis integrations shall have integration tests.

CI tests shall use mock providers and shall not call paid providers.

### NFR-07 — Code quality

Ruff, mypy and pytest shall pass before a pull request is merged.

Critical business-logic modules shall target at least 80% test coverage.

### NFR-08 — Deployment

The API, PostgreSQL and Redis shall start through Docker Compose.

The system shall support development on Apple Silicon.

### NFR-09 — Database management

Database schema changes shall be managed through Alembic migrations.

Application code shall not manually create production tables during
startup.

### NFR-10 — Configuration

Environment-specific behavior shall be configurable without changing
business logic.

A documented `.env.example` shall be committed without real secrets.

## 8. Key acceptance scenarios

### AC-01 — Successful request

Given a valid API key and valid messages  
When the client calls `POST /v1/chat/completions`  
Then the API returns HTTP 200 with request, provider, model and usage data.

### AC-02 — Invalid API key

Given an invalid or revoked API key  
When the client calls the chat API  
Then the API returns HTTP 401 and does not call a provider.

### AC-03 — Successful fallback

Given the primary provider times out  
And the fallback provider is available  
When the gateway processes the request  
Then the API returns HTTP 200 using the fallback provider.

### AC-04 — All providers unavailable

Given both configured providers are unavailable  
When the gateway processes the request  
Then the API returns HTTP 503 with `LLM_PROVIDER_UNAVAILABLE`.

### AC-05 — Rate limit exceeded

Given an API key has sent 30 requests in the current window  
When it sends request 31  
Then the API returns HTTP 429 with `Retry-After`.

### AC-06 — Cache hit

Given an eligible response exists in private cache  
When the same API key sends the same canonical request  
Then the cached response is returned without calling a provider.

### AC-07 — Redis unavailable

Given Redis is unavailable and PostgreSQL is available  
When the client sends a valid chat request  
Then the API continues processing without cache  
And readiness reports HTTP 200 with status `degraded`.

### AC-08 — Usage persistence failure

Given a provider successfully generates a response  
And saving usage metadata fails  
When the gateway completes the request  
Then the client still receives HTTP 200  
And the persistence failure is logged and counted.

## 9. Assumptions

- The gateway is primarily an internal service.
- At least one valid provider credential is available.
- PostgreSQL is the source of truth for API keys and usage.
- Redis is a non-critical dependency.
- Provider pricing is configured manually in USD.
- Provider billing is the final source of truth.
- Provider calls are mocked in CI and most load tests.
- The MVP runs one API instance locally and in staging.
- The client does not enable caching for sensitive data.
- Server-side policy makes the final caching decision.
- The MVP cannot detect all forms of PII.
- Benchmark results must come from real test runs.

## 10. Constraints

- Development duration is four weeks.
- Expected effort is approximately 3–4 hours per day, six days per week.
- Cloud and provider costs must remain low.
- Development primarily uses an Apple Silicon Mac.
- No real secrets may be committed.
- The project demonstrates production engineering practices but is not
  certified as a production service.

## 11. Product decisions

- The MVP does not support streaming.
- Rate limit is 30 requests per minute per API key.
- Cache TTL is 600 seconds.
- Cache is isolated by API key.
- Each provider attempt has a 10-second timeout.
- The primary provider may be retried once.
- Total request deadline is 25 seconds.
- Usage retention target is 90 days.
- API keys are created through CLI and shown once.
- Background workers are deferred to the roadmap.
- Redis failure results in degraded operation.
- PostgreSQL failure results in not-ready status.

## 12. Open questions

The following questions may be resolved later without blocking initial
implementation:

1. Which platform will host the staging environment?
2. Will Langfuse be included after core metrics and logging are complete?

## 13. Definition of Done

The MVP is complete when:

- Docker Compose starts the required services.
- Database migrations run successfully from a clean database.
- A CLI-generated API key can call the chat endpoint.
- OpenAI and Gemini adapters implement the common interface.
- Timeout, retry and fallback behavior is tested.
- Cache and rate limiting behavior is tested.
- Usage and estimated cost are recorded.
- Required health endpoints work.
- CI passes linting, type checking and tests.
- Load and failure tests produce real reports.
- Setup, architecture and operations are documented.