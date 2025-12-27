#!/usr/bin/env bash
set -euo pipefail
kubectl apply -k k8s/
echo "Applied k8s manifests via kustomize"
