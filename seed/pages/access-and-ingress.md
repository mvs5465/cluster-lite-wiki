---
title: Access And Ingress
slug: access-and-ingress
---
The cluster is exposed through an NGINX ingress controller and local `.lan` hostnames.

## Local Access Setup

To reach the cluster from the host machine:

```bash
sudo kubectl port-forward -n ingress-nginx svc/nginx-ingress-ingress-nginx-controller 80:80 443:443
```

Then make sure `/etc/hosts` includes:

```text
127.0.0.1 *.lan
```

## Ingress Controller

- Controller: `ingress-nginx`
- Namespace: `ingress-nginx`
- Service type: `LoadBalancer`
- Purpose: route all browser-facing apps behind a single entry point

## Common Endpoints

| Host | Service |
| --- | --- |
| `homepage.lan` | Homepage dashboard |
| `home.lan` | Cluster Home |
| `wiki.lan` | Cluster Lite Wiki |
| `gatus.lan` | Gatus status page |
| `jellyfin.lan` | Jellyfin |
| `outline.lan` | Outline |
| `chat.lan` | Open WebUI |
| `info.lan` | Cluster Query Router |
| `prometheus.lan` | Prometheus UI |
| `grafana.lan` | Grafana |
| `loki-mcp.lan` | Loki MCP service |
| `prometheus-mcp.lan` | Prometheus MCP service |

## Internal Service Pattern

External requests terminate at NGINX, then route to namespace-local ClusterIP services. Internal service-to-service traffic stays on cluster DNS names such as:

- `prometheus-server.monitoring.svc.cluster.local`
- `loki.monitoring.svc.cluster.local`
- `homepage.services.svc.cluster.local`
- `ollama-external.ai.svc.cluster.local`

This keeps public access simple while allowing internal dependencies to use stable service discovery.
