# Observability Guide

## Overview

ContextPilot ships with backend instrumentation and an optional local observability stack for metrics dashboards and alert rule validation.

Implemented backend instrumentation includes:

- Structured request logging with request IDs and response times
- Prometheus metrics endpoint at `/metrics`
- HTTP metrics:
  - `contextpilot_http_requests_total`
  - `contextpilot_http_request_duration_seconds`
  - `contextpilot_http_active_requests`
- AI metrics:
  - `contextpilot_ai_requests_total`
  - `contextpilot_ai_request_duration_seconds`

---

## Runtime Configuration

Backend environment variables:

- `CONTEXTPILOT_LOG_LEVEL` (default `INFO`)
- `CONTEXTPILOT_LOG_FORMAT` (`json` or `text`, default `json`)
- `CONTEXTPILOT_ENABLE_METRICS` (`true` or `false`, default `true`)

When metrics are disabled, `/metrics` returns `404`.

---

## Local Observability Stack

A local Prometheus + Grafana stack is provided in [observability/docker-compose.yml](../observability/docker-compose.yml).

### Start stack

```bash
cd observability
docker compose up -d
```

### Services

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001` (default login `admin` / `admin`)

### Backend target

Prometheus scrapes:

- `host.docker.internal:8000/metrics`

If your Docker setup cannot resolve `host.docker.internal`, replace the target in [observability/prometheus/prometheus.yml](../observability/prometheus/prometheus.yml) with your reachable backend host/IP.

---

## Dashboard and Alerts

### Provisioned dashboard

- [observability/grafana/dashboards/contextpilot-overview.json](../observability/grafana/dashboards/contextpilot-overview.json)

Covers:

- request rate
- 5xx error ratio
- p95 latency
- in-flight requests
- AI requests by provider
- AI error ratio

### Alert rules

- [observability/prometheus/alerts.yml](../observability/prometheus/alerts.yml)

Current alerts:

- `ContextPilotHigh5xxRate`
- `ContextPilotHighP95Latency`
- `ContextPilotAIErrorSpike`

---

## Triage Runbook

### 1) High 5xx error rate

1. Open Grafana `ContextPilot Overview`
2. Confirm 5xx ratio panel and request-rate spikes
3. Correlate with backend logs using request IDs
4. Check most frequent failing endpoint in Prometheus (`contextpilot_http_requests_total` grouped by path/status)
5. Mitigate (rollback, config fix, provider fallback)

### 2) High p95 latency

1. Validate if traffic surge exists (request rate panel)
2. Identify slow endpoint family
3. Verify AI provider latency trend (`contextpilot_ai_request_duration_seconds`)
4. Confirm DB/system pressure
5. Apply mitigation (scale, cache tuning, provider/model switch)

### 3) AI error spike

1. Inspect AI error ratio panel
2. Break down `contextpilot_ai_requests_total` by provider + status
3. Check key/configuration issues vs provider outage
4. Route to fallback provider when possible

---

## Validation Checklist

- Backend running with metrics enabled
- `/metrics` returns content
- Prometheus target is `UP`
- Grafana dashboard panels populated
- Alert expressions evaluate without query errors

