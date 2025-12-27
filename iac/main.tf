provider "kubernetes" {
  config_path = "~/.kube/config"
}

module "base" {
  source = "./modules/base"
  namespace = var.k8s_namespace
}

module "observability" {
  source = "./modules/observability"
  namespace = var.k8s_namespace
}

module "control" {
  source = "./modules/control"
  namespace = var.k8s_namespace
}
