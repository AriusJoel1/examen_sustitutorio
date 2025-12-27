#!/usr/bin/env bash
set -euo pipefail
mkdir -p ./evidence

pushd iac >/dev/null
terraform init -input=false -backend-config=backend.tf || true

# terraform plan returns 2 when changes present (detailed-exitcode)
terraform plan -input=false -detailed-exitcode -out=tfplan.binary
PLAN_EXIT=$?
if [ "$PLAN_EXIT" -eq 2 ]; then
  echo "DRIFT_DETECTED" | tee ../evidence/drift_detected.txt
  terraform show -no-color tfplan.binary > ../evidence/plan_diff.txt
  echo "Plan saved to evidence/plan_diff.txt"
  exit 2
elif [ "$PLAN_EXIT" -eq 0 ]; then
  echo "NO_DRIFT" | tee ../evidence/no_drift.txt
  exit 0
else
  echo "ERR_PLAN_EXIT=${PLAN_EXIT}"
  exit $PLAN_EXIT
fi
popd >/dev/null
