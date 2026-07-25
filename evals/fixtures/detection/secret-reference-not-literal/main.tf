# Provider credentials come from a Terraform variable, not a committed literal.
provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

variable "cloudflare_api_token" {
  type      = string
  sensitive = true
}
