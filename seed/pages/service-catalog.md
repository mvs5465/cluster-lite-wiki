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
| Prometheus Operator CRDs | `monitoring` | Required CRDs for Prometheus ecosystem |
| Prometheus | `monitoring` | Metrics collection, retention, and query UI |
| Grafana | `monitoring` | Dashboards and visual analysis |
| Loki | `monitoring` | Log aggregation backend |
| Promtail | `monitoring` | Log shipping agent |
| NGINX Ingress | `ingress-nginx` | Shared ingress layer |

## User-Facing Services

| Service | Namespace | Host | Purpose |
| --- | --- | --- | --- |
| Homepage | `services` | `homepage.lan` | Main service dashboard |
| Cluster Home | `services` | `home.lan` | Custom dashboard with curated links |
| Cluster Lite Wiki | `services` | `wiki.lan` | Lightweight internal docs |
| Gatus | `services` | `gatus.lan` | Uptime checks and status |
| Jellyfin | `services` | `jellyfin.lan` | Media library and streaming |
| Outline | `outline` | `outline.lan` | Rich wiki and collaboration |

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

- `Cluster Home` and `Homepage` overlap as navigation layers, but they serve different UX goals.
- `Cluster Lite Wiki` is optimized for fast browser editing and operational notes.
- `Outline` remains the heavier, collaborative long-form knowledge base.
