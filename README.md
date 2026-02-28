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

On first boot, if the database is empty, the app imports the Markdown files in `seed/pages/`.
This bootstrap runs only once for a given database and does not overwrite existing pages.

To intentionally replace the current database contents with the seed files, run:

```bash
python app.py reseed
```

This deletes existing pages in the target database and reloads everything from `seed/pages/`.

## Kubernetes Reseed Job

To reseed the live wiki in Kubernetes, apply the one-off job manifest in [k8s/wiki-reseed-job.yaml](k8s/wiki-reseed-job.yaml):

```bash
kubectl apply -f k8s/wiki-reseed-job.yaml
kubectl logs -n services job/wiki-reseed -f
```

When the job completes, remove it so it can be re-run later with the same name:

```bash
kubectl delete job -n services wiki-reseed
```

The job mounts the `cluster-lite-wiki-data` PVC at `/data` and runs `python app.py reseed`.
It is destructive: existing wiki pages in that database are deleted and replaced with the current seed files.

## Kubernetes

The Helm chart lives in `chart/`. To persist data with a standard Kubernetes PVC, set:

```yaml
persistence:
  enabled: true
  size: 1Gi
  mountPath: /data
```

The chart creates a `PersistentVolumeClaim` and relies on the cluster's default storage class
to provision backing storage unless you set `persistence.storageClassName` or `persistence.existingClaim`.
