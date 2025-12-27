output "namespace" {
  description = "Kubernetes namespace created for the app"
  value       = module.base.namespace
}

output "kubeconfig_path" {
  description = "Path to kubeconfig used (if any)"
  value       = coalescelist([var.kubeconfig_path], ["~/.kube/config"])[0]
}
