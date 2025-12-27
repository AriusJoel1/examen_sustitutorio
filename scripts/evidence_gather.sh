#!/usr/bin/env bash
set -euo pipefail
mkdir -p evidence
kubectl -n agua-inteligente get deployments > evidence/k8s_deployments.txt
kubectl -n agua-inteligente get pods -o wide > evidence/k8s_pods.txt
kubectl -n agua-inteligente get networkpolicies -o yaml > evidence/k8s_netpols.yaml
kubectl -n agua-inteligente get rolebinding,role -o yaml > evidence/k8s_rbac.yaml
