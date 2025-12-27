terraform {
  required_version = ">= 1.0"
  backend "local" {
    path = "../.tfstate/terraform.tfstate"
  }
}
