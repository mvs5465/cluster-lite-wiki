---
title: Observability And Debugging
slug: observability-and-debugging
---
Observability in this cluster is split across metrics, dashboards, logs, and health checks.

## Metrics

Prometheus runs in `monitoring` and provides:

- 7 day retention
- Persistent storage with a 2Gi volume
- Node exporter enabled
- kube-state-metrics enabled
- extra scrape targets for ArgoCD controller, application set, repo server, and server metrics

Primary UI:

- `http://prometheus.lan`

## Dashboards

Grafana runs in `monitoring` and loads dashboard definitions from the applications repo, including:

- cluster overview
- Loki metrics
- pod metrics
- ArgoCD overview

Primary UI:

- `http://grafana.lan`

## Logs

Loki runs in single-binary mode with filesystem storage and a 24 hour retention window.

- Backend: `loki.monitoring.svc.cluster.local:3100`
- Ingress: disabled
- Intended use: internal log storage queried by Grafana and tooling

Promtail ships logs into Loki from the cluster.

## Health Checks

Gatus runs in `services` and probes core internal endpoints on a 60 second interval:

- Prometheus
- Grafana
- Loki
- Homepage
- ArgoCD
- Gatus
- Jellyfin
- Outline
- Chat
- Ollama

Primary UI:

- `http://gatus.lan`

## MCP Access

Two MCP-facing services expose observability systems for tool-assisted querying:

- `http://prometheus-mcp.lan`
- `http://loki-mcp.lan`

These are intended for LLM or tool integrations that need structured access to metrics and logs.
