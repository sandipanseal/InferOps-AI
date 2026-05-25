variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "eu-central-1"
}

variable "environment" {
  description = "Environment name (used in resource names and the ENVIRONMENT env var)"
  type        = string
  default     = "aws-deploy"
}

variable "project_name" {
  description = "Project name prefix for all resource names"
  type        = string
  default     = "inferops"
}

variable "frontend_subdomain" {
  description = "Optional Route53 subdomain for the frontend (leave empty to use the default cloudfront.net URL)"
  type        = string
  default     = ""
}

# ── Secrets — provided via aws-deploy.tfvars ─────────────────────────────────

variable "database_url" {
  description = "Supabase Postgres connection string (sync — used by Lambda runtime via psycopg2)"
  type        = string
  sensitive   = true
}

variable "redis_url" {
  description = "Upstash Redis URL (rediss://...)"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key — used only for quality_optimized + high-complexity routes"
  type        = string
  sensitive   = true
}

variable "ollama_cloud_api_key" {
  description = "Ollama Cloud API key — primary cost-optimized provider"
  type        = string
  sensitive   = true
  default     = ""
}

variable "ollama_cloud_base_url" {
  description = "Ollama Cloud API base URL"
  type        = string
  default     = "https://ollama.com"
}

variable "ollama_cloud_model" {
  description = "Default Ollama Cloud model name"
  type        = string
  default     = "gpt-oss:120b-cloud"
}

variable "langfuse_public_key" {
  description = "Langfuse public key (optional)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "langfuse_secret_key" {
  description = "Langfuse secret key (optional)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "langfuse_host" {
  description = "Langfuse host URL"
  type        = string
  default     = "https://cloud.langfuse.com"
}
