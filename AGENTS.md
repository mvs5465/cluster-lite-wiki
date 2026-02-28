# Cluster Lite Wiki

## Scope
- Lightweight Flask wiki app with server-rendered templates and a Helm chart for Kubernetes deployment.
- Prefer small, direct changes that keep the app easy to run locally and easy to deploy through ArgoCD.

## Local Development
- Use the existing virtualenv at `.venv` when available.
- For rapid UI iteration, run the app with Flask debug reload:
  - `.venv/bin/python -m flask --app app:create_app --debug run --host 0.0.0.0 --port 8080`
- Default local data lives in `./data/wiki.db`.

## App Changes
- Keep dependencies minimal unless there is a clear reason to add one.
- Preserve the current server-rendered Flask approach unless a larger architecture change is explicitly requested.
- Prefer editing templates and `static/styles.css` directly for UI changes rather than adding client-side complexity.

## Storage
- The chart should default to a standard dynamically provisioned PVC.
- Do not introduce a chart-managed `PersistentVolume` unless explicitly requested and validated against ArgoCD project permissions.
- When changing persistence behavior, verify the rendered Helm manifests and confirm how the target storage class behaves in-cluster.

## Helm And Releases
- If a PR changes anything under `chart/`, bump `chart/Chart.yaml` `version` in that same PR.
- Bump `appVersion` when the deployed application release meaningfully changes.
- Treat chart and app versions as release metadata, not deployment selectors; ArgoCD deploys from `main`.
- Use loose semver tracking:
  - bump `version` for chart changes, usually patch unless the chart interface changes materially
  - bump `appVersion` for meaningful app changes, including UI, seeding, or behavior changes
  - keeping `version` and `appVersion` aligned is acceptable when that is the simplest honest representation
- Keep chart changes compatible with ArgoCD-managed sync in the `cluster` AppProject.

## Verification
- For chart changes, run `helm template cluster-lite-wiki ./chart`.
- For app changes, verify the app still serves locally.
- If tests are needed, use `pytest` when available in the environment.
