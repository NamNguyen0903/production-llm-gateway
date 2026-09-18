# Production LLM Gateway API Design

## 1. Document Information

- Status: Proposed
- Related ticket: AI-103
- API version: v1
- Last updated: 2026-09-18

## 2. API Conventions

The API uses:

- JSON request and response bodies
- Versioned paths
- UTF-8 text
- UTC timestamps
- Stable machine-readable error codes
- A gateway-generated request ID for every request

Base API prefix:

```text
/v1
```

## 3. Authentication

Protected endpoints require:

```http
Authorization: Bearer llmgw_live_example
```

API keys must not be supplied through:

- URL query parameters
- Request bodies
- Cookies
- Log messages

Missing or invalid API keys return HTTP 401.

## 4. Request Correlation

The gateway always creates a trusted internal request ID:

```text
req_01JXYZ...
```

The response contains:

```http
X-Request-ID: req_01JXYZ
```

A client may optionally send:

```http
X-Client-Request-ID: client-correlation-123
```

The client correlation ID:

- Must not replace the internal request ID
- Must be validated
- Must have a maximum length
- Must not be used as a primary key
- Must not contain secrets

## 5. POST /v1/chat/completions

Creates a non-streaming chat completion.

### 5.1 Request headers

```http
POST /v1/chat/completions
Authorization: Bearer llmgw_live_example
Content-Type: application/json
X-Client-Request-ID: optional-client-id
```

### 5.2 Request body

```json
{
  "model": "auto",
  "messages": [
    {
      "role": "system",
      "content": "Answer clearly and concisely."
    },
    {
      "role": "user",
      "content": "Explain Redis in simple terms."
    }
  ],
  "temperature": 0.2,
  "max_tokens": 500,
  "stream": false,
  "cache": true,
  "sensitive": false
}
```

### 5.3 Request fields

| Field | Type | Required | Default | Validation |
|---|---|---:|---|---|
| `model` | string | No | `auto` | Must be `auto` or allowed model |
| `messages` | array | Yes | — | At least one message |
| `messages.role` | string | Yes | — | `system`, `user`, `assistant` |
| `messages.content` | string | Yes | — | Non-empty |
| `temperature` | decimal | No | `0.2` | Between 0 and 2 |
| `max_tokens` | integer | No | Gateway config | Between 1 and 4096 |
| `stream` | boolean | No | `false` | MVP accepts only `false` |
| `cache` | boolean | No | `false` | Boolean |
| `sensitive` | boolean | No | `false` | Boolean |

### 5.4 Request limits

Initial gateway limits:

```text
Maximum HTTP body: 1 MB
Maximum messages: 50
Maximum characters per message: 20,000
Maximum requested output: 4,096 tokens
```

Provider-specific limits are hidden behind the gateway.

### 5.5 Model behavior

If `model` is omitted:

```text
model = auto
```

The gateway applies deterministic routing.

If a specific model is provided:

1. The model must exist in the gateway allowlist.
2. The model must be enabled.
3. The gateway maps it to the correct provider.
4. Unsupported models return HTTP 400.

## 6. Validation Rules

### Streaming

The MVP does not support streaming.

Request:

```json
{
  "stream": true
}
```

Response:

```text
HTTP 422
STREAMING_NOT_SUPPORTED
```

### Conflicting cache policy

The following combination is invalid:

```json
{
  "cache": true,
  "sensitive": true
}
```

Response:

```text
HTTP 422
CONFLICTING_CACHE_POLICY
```

The server fails explicitly instead of silently changing client behavior.

## 7. Successful Response

```json
{
  "id": "req_01JXYZ",
  "object": "chat.completion",
  "created": 1789699200,
  "provider": "gemini",
  "model": "configured-fallback-model",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Redis is a fast in-memory data store."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 80,
    "total_tokens": 105,
    "estimated_cost_usd": "0.000125"
  },
  "gateway": {
    "cache_requested": true,
    "cache_eligible": true,
    "cache_hit": false,
    "fallback_used": true,
    "retry_count": 0
  }
}
```

The format is intentionally similar to common OpenAI-style responses but
is owned and normalized by the gateway.

Provider SDK response objects must not be returned directly.

## 8. Cache-Hit Response

A cache hit returns a new internal request ID.

It must not reuse the ID of the request that originally generated the
cached response.

```json
{
  "id": "req_new_request_id",
  "object": "chat.completion",
  "created": 1789699300,
  "provider": "gemini",
  "model": "configured-model",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Cached content."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
    "estimated_cost_usd": "0"
  },
  "gateway": {
    "cache_requested": true,
    "cache_eligible": true,
    "cache_hit": true,
    "fallback_used": false,
    "retry_count": 0
  }
}
```

The usage values describe new provider usage created by the current
request, not the original generation.

## 9. Error Response

All gateway errors use the following structure:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please retry later.",
    "request_id": "req_01JXYZ",
    "retryable": true,
    "details": null
  }
}
```

### Error fields

| Field | Purpose |
|---|---|
| `code` | Stable value used by client logic |
| `message` | Human-readable explanation |
| `request_id` | Correlates the response with logs |
| `retryable` | Indicates whether retry may succeed |
| `details` | Safe structured validation details |

Clients should branch on `code`, not on `message`.

## 10. Error Catalogue

| HTTP | Code | Retryable | Meaning |
|---:|---|---:|---|
| 400 | `UNSUPPORTED_MODEL` | No | Model is not allowed |
| 401 | `MISSING_API_KEY` | No | Authentication header is missing |
| 401 | `INVALID_API_KEY` | No | Key is invalid, expired or revoked |
| 413 | `PAYLOAD_TOO_LARGE` | No | Request body exceeds the limit |
| 422 | `VALIDATION_ERROR` | No | Request data is invalid |
| 422 | `STREAMING_NOT_SUPPORTED` | No | Streaming is outside MVP |
| 422 | `CONFLICTING_CACHE_POLICY` | No | Sensitive request enabled caching |
| 429 | `RATE_LIMIT_EXCEEDED` | Yes | API-key limit has been reached |
| 500 | `INTERNAL_ERROR` | Maybe | Unexpected internal failure |
| 503 | `LLM_PROVIDER_UNAVAILABLE` | Yes | All providers failed |
| 503 | `SERVICE_NOT_READY` | Yes | Critical dependency is unavailable |
| 504 | `REQUEST_DEADLINE_EXCEEDED` | Yes | Total request deadline expired |

Provider exceptions, database errors and stack traces must not be exposed
to clients.

## 11. Response Headers

Every response includes:

```http
X-Request-ID: req_01JXYZ
```

Rate-limit information may include:

```http
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 18
X-RateLimit-Reset: 1789699260
```

HTTP 429 includes:

```http
Retry-After: 25
```

HTTP 503 may include `Retry-After` only when the gateway has a reliable
retry estimate.

## 12. Health Endpoints

### GET /health/live

Indicates whether the API process is alive.

Success:

```json
{
  "status": "alive"
}
```

HTTP status: `200`.

### GET /health/ready

Healthy:

```json
{
  "status": "ready",
  "dependencies": {
    "postgresql": "available",
    "redis": "available"
  }
}
```

HTTP status: `200`.

Redis unavailable:

```json
{
  "status": "degraded",
  "dependencies": {
    "postgresql": "available",
    "redis": "unavailable"
  }
}
```

HTTP status: `200`.

PostgreSQL unavailable:

```json
{
  "status": "not_ready",
  "dependencies": {
    "postgresql": "unavailable",
    "redis": "available"
  }
}
```

HTTP status: `503`.

Health responses must not contain credentials, connection strings or
internal hostnames.

## 13. Metrics Endpoint

```http
GET /metrics
```

The endpoint is intended for Prometheus and is not a public client API.

Staging and production deployments must restrict access using an
internal network, reverse proxy policy or monitoring authentication.

## 14. Decimal Representation

Money values are returned as decimal strings:

```json
{
  "estimated_cost_usd": "0.000125"
}
```

The implementation uses Python `Decimal` and PostgreSQL `NUMERIC`.

## 15. Security Considerations

The API must not expose:

- Raw API keys
- Provider credentials
- Database credentials
- Provider SDK exceptions
- Stack traces
- Complete prompts in logs
- Complete generated responses in logs

## 16. MVP Limitations

The API does not support:

- Streaming
- Idempotency keys
- Tool calling
- Multimodal messages
- RAG
- Agent execution
- Administrative HTTP endpoints