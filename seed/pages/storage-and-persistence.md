---
title: Storage And Persistence
slug: storage-and-persistence
---
Storage is a mix of standard Kubernetes PVCs and explicit host-mounted paths exposed through Colima.

## Colima Mounts

The recommended Colima startup command mounts:

```bash
colima start --kubernetes --cpu 4 --memory 6 \
  --mount ~/clusterstorage:w \
  --mount ~/.secrets:/mnt/secrets:ro
```

That makes `~/clusterstorage` the durable host-backed location for selected workloads.

## Host-Backed Paths

Current host-mounted data paths include:

| Path | Used By |
| --- | --- |
| `~/clusterstorage/files` | Jellyfin media files |
| `~/clusterstorage/outline/files` | Outline uploaded files |
| `~/clusterstorage/outline/postgres` | Outline PostgreSQL data |

These survive cluster recreation as long as the Colima mount is preserved.

## Dynamic PVCs

The cluster default storage class is `local-path`, provisioned by `rancher.io/local-path`.

Use this when:

- the app only needs regular persistent storage
- ArgoCD should manage a simple PVC without extra cluster-scoped resources
- there is no requirement to pin data to a named host directory

This is the current storage model for Cluster Lite Wiki.

## Service-Specific Notes

- Prometheus uses a 2Gi persistent volume for metrics retention.
- Loki uses a 1Gi persistent volume in single-binary mode.
- Gatus stores its SQLite database under `/data/gatus.db` on a PVC.
- Outline mixes hostPath storage for long-lived files and PostgreSQL with `emptyDir` for Redis.

## Operational Guidance

- Prefer standard PVCs first.
- Only use explicit host paths when you need a stable, human-named location under `~/clusterstorage`.
- Be careful introducing static `PersistentVolume` objects through ArgoCD because AppProject policy may block cluster-scoped resources.
