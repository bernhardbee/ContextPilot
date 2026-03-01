# Local Observability Stack

This folder contains a local Prometheus + Grafana stack for ContextPilot.

## Files

- `docker-compose.yml`: local stack launcher
- `prometheus/prometheus.yml`: scrape config
- `prometheus/alerts.yml`: alert rules
- `grafana/provisioning/*`: datasource + dashboard provisioning
- `grafana/dashboards/contextpilot-overview.json`: default dashboard

## Quick Start

```bash
cd observability
docker compose up -d
```

Then open:

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

Default Grafana credentials:

- Username: `admin`
- Password: `admin`

For full guidance, see [docs/OBSERVABILITY.md](../docs/OBSERVABILITY.md).
