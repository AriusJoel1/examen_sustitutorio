resource "kubernetes_namespace" "appns" {
  metadata {
    name = var.namespace
    labels = {
      "env" = var.namespace
    }
  }
}

output "namespace" {
  value = kubernetes_namespace.appns.metadata[0].name
}
