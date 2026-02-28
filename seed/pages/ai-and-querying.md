---
title: AI And Querying Stack
slug: ai-and-querying
---
The AI side of the cluster is designed to provide a local chat interface plus tool-aware cluster querying.

## Chat Path

The user-facing chat entry point is Open WebUI:

- Service: `chat`
- Namespace: `ai`
- Host: `chat.lan`

It points at:

- `OLLAMA_BASE_URL=http://ollama-mcp-bridge.ai.svc.cluster.local:8000`

Authentication is currently disabled for local use:

- `WEBUI_AUTH=false`

## Ollama Bridge

`ollama-mcp-bridge` is the tool-aware adapter between chat and the model endpoint.

- Namespace: `ai`
- Internal port: `8000`
- Upstream model endpoint: `http://ollama-external.ai.svc.cluster.local:11434`

It also mounts an MCP configuration that currently includes:

- Prometheus MCP
- Loki MCP

That lets model requests reach cluster metrics and logs through a structured tool layer.

## Cluster Query Router

`cluster-query-router` is exposed at `info.lan` and centralizes cluster-oriented query routing.

Configured upstream dependencies:

- Loki MCP: `http://loki-mcp.monitoring.svc.cluster.local:8000`
- Prometheus MCP: `http://prometheus-mcp.monitoring.svc.cluster.local:8080`
- Ollama: `http://ollama-external.ai.svc.cluster.local:11434`

## MCP Services

| Service | Namespace | Purpose |
| --- | --- | --- |
| Prometheus MCP | `monitoring` | Structured metrics access |
| Loki MCP | `monitoring` | Structured log access |

Together, these services support a local AI workflow where cluster context is available through tools instead of only raw prompt text.
