---
title: GitOps And Repos
slug: gitops-and-repos
---
This cluster uses a two-repo GitOps model to keep infrastructure and application changes separate.

## Repositories

| Repo | Role |
| --- | --- |
| `local-k8s-argocd` | Installs and manages ArgoCD, AppProject config, and the bootstrap `ApplicationSet` |
| `local-k8s-apps` | Declares the system and user-facing `Application` specs used as `ApplicationSet` input |
| App repos (for example `cluster-lite-wiki`, `cluster-home`, `cluster-query-router`) | Hold app code, images, and Helm charts |

## Why Two Repos

- Prevents a chicken-and-egg problem while ArgoCD manages itself
- Keeps infrastructure changes stable
- Lets application repos iterate more freely
- Makes it clear where app definitions live versus where app code lives

## Sync Model

1. Push changes to a feature branch.
2. Open a PR.
3. Merge to `main`.
4. ArgoCD detects the new revision and syncs automatically.

For app repos that provide a chart directly from GitHub, the repo URL must be whitelisted in the `cluster` AppProject.
The bootstrap `ApplicationSet` then regenerates the live `Application` objects in rollout stages.

## Current Repo Relationships

- `cluster-lite-wiki` application points to the `cluster-lite-wiki` repo `chart/` path
- `cluster-home` application points to the `cluster-home` repo `chart/` path
- `cluster-query-router` application points to the `cluster-query-router` repo `chart/` path
- `loki-mcp` application points to the `loki-mcp-server` repo `chart/` path

## Release Discipline

- Application repos use feature branches and PRs by default
- ArgoCD watches `main`
- Chart changes should bump `chart/Chart.yaml` version in the same PR

This wiki should evolve alongside that flow so the cluster docs stay close to the actual deployment configuration.
