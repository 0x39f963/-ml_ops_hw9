variable "environment" {
  type        = string
  description = "Environment name for demo resources."
  default     = "dev"
}

variable "artifact_root" {
  type        = string
  description = "Local demo path for generated infrastructure manifests."
  default     = "../.infra_artifacts"
}

variable "inventory_bucket_name" {
  type        = string
  description = "Logical bucket name for inventory batches."
  default     = "inventory-batches"
}
