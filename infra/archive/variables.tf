variable "region" {
  type        = string
  description = "Explicit region. Must offer Bedrock KB, S3 Vectors, Guardrails Standard tier and AgentCore Gateway."
}

variable "name" {
  type    = string
  default = "skynet-archive"
}

variable "scenario" {
  type        = string
  default     = "cyberdyne-chip"
  description = "Scenario the Gateway tool filters to. All four are ingested."
}

variable "embedding_model_id" {
  type    = string
  default = "amazon.titan-embed-text-v2:0"
}

variable "embedding_dimensions" {
  type    = number
  default = 1024
}

variable "guardrail_profile" {
  type        = string
  default     = "us.guardrail.v1:0"
  description = "Guardrail profile for Standard tier cross-region inference; match it to the region."
}

variable "aws_profile" {
  type        = string
  default     = ""
  description = "Named profile for both the provider and the ingestion CLI call. Empty = default chain."
}

variable "log_retention_days" {
  type        = number
  default     = 7
  description = "Lambda log retention. The evidence bundle on disk is the long-term record."
}

variable "min_score" {
  type        = string
  default     = "0.60"
  description = "Semantic results scoring below this are dropped as noise (10. Oct 2026 probe: relevant >= ~0.70, off-topic 0.52-0.55)."
}
