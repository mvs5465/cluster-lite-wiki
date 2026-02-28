# Cluster Lite Wiki

A lightweight self-hosted wiki for small Kubernetes clusters.

## Features

- Browser-based page creation and editing
- Markdown rendering
- SQLite persistence in a single local file
- Simple full-text search using SQLite queries
- One-container deployment with a built-in Helm chart

## Local Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

The app listens on `http://127.0.0.1:8080` by default and stores data in `./data/wiki.db`.

## Kubernetes

The Helm chart lives in `chart/`. To persist data on the shared Colima-mounted storage, set:

```yaml
persistence:
  enabled: true
  hostPath: /Users/matthewschwartz/clusterstorage/wiki/data
  mountPath: /data
```
