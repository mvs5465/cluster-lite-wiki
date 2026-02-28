---
title: Service Catalog
slug: service-catalog
---
This page is the quick inventory of what is running in the cluster and why.

## Infrastructure And Monitoring

| Service | Namespace | Purpose |
| --- | --- | --- |
| ArgoCD | `argocd` | GitOps deployment control plane |
| External Secrets | `external-secrets` | Syncs secret data into the cluster |
| Grafana Kubernetes Monitoring | `monitoring` | Alloy-managed metrics, events, and log collection |
| Prometheus | `monitoring` | Metrics backend, retention, and query UI |
| Grafana | `monitoring` | Dashboards and visual analysis |
| Loki | `monitoring` | Log aggregation backend |
| NGINX Ingress | `ingress-nginx` | Shared ingress layer |

## User-Facing Services

| Service | Namespace | Host | Purpose |
| --- | --- | --- | --- |
| Cluster Home | `services` | `home.lan` | Main custom dashboard with curated links |
| Cluster Lite Wiki | `services` | `wiki.lan` | Lightweight internal docs |
| Gatus | `services` | `gatus.lan` | Uptime checks and status |
| Jellyfin | `services` | `jellyfin.lan` | Media library and streaming |

## AI And Tooling

| Service | Namespace | Host | Purpose |
| --- | --- | --- | --- |
| Chat (Open WebUI) | `ai` | `chat.lan` | Browser chat interface |
| Cluster Query Router | `ai` | `info.lan` | Routes cluster-oriented queries |
| Ollama MCP Bridge | `ai` | internal | Bridges model calls to MCP tools |
| Ollama External | `ai` | internal | Cluster-facing service for native Ollama |
| Prometheus MCP | `monitoring` | `prometheus-mcp.lan` | Metrics access through MCP |
| Loki MCP | `monitoring` | `loki-mcp.lan` | Log access through MCP |

## Notes

- `Cluster Home` is the primary navigation layer for the local cluster.
- `Cluster Lite Wiki` is optimized for fast browser editing and operational notes.
