package kubernetes.admission

deny[msg] {
  input.request.kind.kind == "Deployment"
  replicas := input.request.object.spec.replicas
  replicas > 1
  not input.request.object.metadata.labels.approved
  msg = sprintf("Scaling to %v replicas is forbidden without 'approved' label", [replicas])
}
