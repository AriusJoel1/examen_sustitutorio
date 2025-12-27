package test.scale

deny[msg] {
  input.kind == "Deployment"
  replicas := input.spec.replicas
  replicas > 1
  not input.metadata.labels.approved
  msg = sprintf("Deployment %v tries to set replicas=%v without approved label", [input.metadata.name, replicas])
}
