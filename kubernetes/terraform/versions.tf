terraform {
  required_version = ">= 1.3"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"  # Use AWS provider 5.x instead of 6.x
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"  # Use Helm provider 2.x instead of 3.x
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
  }
}
