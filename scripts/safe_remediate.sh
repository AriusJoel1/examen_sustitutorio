#!/usr/bin/env bash
set -euo pipefail
RESOURCE=${1:-}
if [ -z "$RESOURCE" ]; then
  echo "Usage: $0 <tf_resource_address>"
  exit 1
fi

pushd iac >/dev/null
terraform init -input=false || true
terraform apply -input=false -target=${RESOURCE} -auto-approve
popd >/dev/null

echo "Remediation applied to ${RESOURCE}" > ./evidence/remediation_${RESOURCE//[/].txt
