---
title: Observability And Debugging
slug: observability-and-debugging
---
Observability in this cluster is split into a collection layer, storage backends, dashboards, and health checks.

## Collection Layer

Grafana Kubernetes Monitoring runs in `monitoring` and uses Alloy-managed collectors for the cluster.

- `k8s-monitoring` chart from Grafana
- Alloy Operator-managed collectors
- Cluster metrics enabled
- Cluster events enabled
- Pod logs enabled
- Annotation autodiscovery enabled
- Prometheus Operator objects enabled for ServiceMonitor-based custom scrapes

ArgoCD metrics are brought in through ServiceMonitors instead of ad hoc static scrape targets.

## Storage And Query

Prometheus remains in `monitoring`, but it now acts as the metrics backend and query UI instead of the primary cluster scraper.

- 7 day retention
- Persistent storage with a 2Gi volume
- Remote write receiver enabled
- Minimal self-scrape config for the Prometheus server itself

Primary UI:

- `http://prometheus.lan`

## Dashboards

Grafana runs in `monitoring` and loads dashboard definitions from the applications repo, including:

- cluster overview
- Loki metrics
- pod deep dive
- ArgoCD overview

Primary UI:

- `http://grafana.lan`

## Logs

Loki runs in single-binary mode with filesystem storage and a 24 hour retention window.

- Backend: `loki.monitoring.svc.cluster.local:3100`
- Ingress: disabled
- Intended use: internal log storage queried by Grafana and tooling

Alloy ships pod logs and cluster events into Loki.

## Health Checks

Gatus runs in `services` and probes core internal endpoints on a 60 second interval:

- Prometheus
- Grafana
- Loki
- Homepage
- ArgoCD
- Gatus
- Jellyfin
- Chat
- Ollama

Primary UI:

- `http://gatus.lan`

## MCP Access

Two MCP-facing services expose observability systems for tool-assisted querying:

- `http://prometheus-mcp.lan`
- `http://loki-mcp.lan`

These are intended for LLM or tool integrations that need structured access to metrics and logs.
