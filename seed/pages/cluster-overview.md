---
title: Cluster Overview
slug: cluster-overview
---
This local Kubernetes environment is a Colima-backed k3s cluster managed through ArgoCD. It is built for day-to-day personal operations: dashboards, media, AI tools, observability, and lightweight internal docs.

## Core Shape

- Runtime: Colima with Kubernetes enabled
- Kubernetes distribution: k3s
- GitOps: ArgoCD watches `main`, applies bootstrap config, and generates app rollouts through an `ApplicationSet`
- Primary hostnames: `*.lan`
- Main entry point: `http://home.lan`

## Topology Diagram

```text
Mac Host
  |
  +-- Colima VM (k3s)
        |
        +-- ingress-nginx
        |     |
        |     +-- *.lan routes
        |
        +-- argocd
        |     |
        |     +-- watches local-k8s-argocd
        |     +-- bootstrap ApplicationSet reads local-k8s-apps
        |
        +-- services
        |     |
        |     +-- cluster-home / cluster-lite-wiki / gatus / jellyfin
        |
        +-- monitoring
        |     |
        |     +-- k8s-monitoring / prometheus / grafana / loki / mcp services
        |
        +-- ai
        |     |
        |     +-- chat / cluster-query-router / ollama bridge
```

## Key Namespaces

| Namespace | Purpose |
| --- | --- |
| `argocd` | GitOps control plane and bootstrap applications |
| `monitoring` | Grafana, Loki, Prometheus, Grafana Kubernetes Monitoring, and MCP services |
| `ingress-nginx` | Shared ingress controller |
| `external-secrets` | Cluster secret synchronization |
| `services` | User-facing web apps and dashboards |
| `ai` | Chat, query router, Ollama bridge, and related tools |

## Main User-Facing Services

| Service | Host | Role |
| --- | --- | --- |
| Cluster Home | `home.lan` | Custom curated dashboard for the cluster |
| Cluster Lite Wiki | `wiki.lan` | Lightweight notes, runbooks, and reference docs |
| Gatus | `gatus.lan` | Health checks and uptime status |
| Jellyfin | `jellyfin.lan` | Media server |
| Chat | `chat.lan` | Open WebUI connected to the local AI stack |
| Cluster Info | `info.lan` | Query routing and cluster context tools |

## Operating Model

1. Infrastructure repo bootstraps ArgoCD and the shared AppProject.
2. The bootstrap `ApplicationSet` reads the applications repo and generates the live services.
3. Individual app repos ship their own charts or images.
4. ArgoCD syncs merged `main` changes automatically.

This wiki is intended to hold the human-readable version of that system: what is deployed, why it exists, and how to operate it.
