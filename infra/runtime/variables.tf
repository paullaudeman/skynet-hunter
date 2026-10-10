variable "region" {
  type        = string
  description = "Explicit region; the archive stack's region."
}

variable "aws_profile" {
  type    = string
  default = ""
}

variable "models" {
  type        = list(string)
  description = "The inference profiles in config.bedrock.toml. Change both together."
  default = [
    "global.anthropic.claude-opus-4-6-v1",
    "global.anthropic.claude-sonnet-4-6",
    "global.anthropic.claude-haiku-4-5-20251001-v1:0",
  ]
}

variable "guardrail_profile" {
  type    = string
  default = "us.guardrail.v1:0"
}

variable "idle_timeout_s" {
  type    = number
  default = 120
}

variable "max_lifetime_s" {
  type    = number
  default = 1800
}
