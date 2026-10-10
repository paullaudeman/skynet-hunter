# The hunt on AgentCore Runtime (Phase 1).
#
#   dist/runtime.zip ─▶ code bucket (S3) ─▶ AgentCore Runtime "skynet_hunt" (ARM64, PYTHON_3_13, direct code deploy)
#   execution role ─▶ Bedrock models (global. profiles) · the archive's KB (Retrieve) · its guardrail (ApplyGuardrail)
#
# The archive stack (infra/archive) must be applied first; this reads its state.
# Before `apply`: ./infra/runtime/build_runtime.sh
#
# Billed: runtime compute while a session is active (CPU and memory per second), Bedrock tokens per hunt, and the
# archive's per-search costs. Nothing bills while idle except a few MB of S3.

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = { source = "hashicorp/aws", version = ">= 6.68" } # code_configuration on the agent runtime
  }
}

provider "aws" {
  region  = var.region
  profile = var.aws_profile == "" ? null : var.aws_profile

  # ~/.claude/reference/aws-deploy-standards.md. Not taggable: the S3 object's ACL, the policy.
  default_tags {
    tags = {
      Project   = "skynet-hunter"
      Component = "agent-runtime"
      Repo      = "github.com/paullaudeman/skynet-hunter"
      Stack     = "infra/runtime"
      ManagedBy = "terraform"
      Owner     = "paul"
      Env       = "demo"
      DataClass = "synthetic"
    }
  }
}

data "aws_caller_identity" "me" {}
data "aws_partition" "p" {}

data "terraform_remote_state" "archive" {
  backend = "local"
  config  = { path = "${path.module}/../archive/terraform.tfstate" }
}

locals {
  account   = data.aws_caller_identity.me.account_id
  part      = data.aws_partition.p.partition
  kb_id     = data.terraform_remote_state.archive.outputs.knowledge_base_id
  guardrail = split(":", data.terraform_remote_state.archive.outputs.guardrail) # [id, version]
  zip       = "${path.module}/dist/runtime.zip"
  # A global. profile routes to any commercial region, so the foundation-model ARN has no region (and, for
  # safety, any region). The profile ARN itself is in this account and region.
  profile_arns = [for m in var.models : "arn:${local.part}:bedrock:${var.region}:${local.account}:inference-profile/${m}"]
  model_arns = flatten([for m in var.models : [
    "arn:${local.part}:bedrock:::foundation-model/${trimprefix(m, "global.")}",
    "arn:${local.part}:bedrock:*::foundation-model/${trimprefix(m, "global.")}",
  ]])
}

# ── code ─────────────────────────────────────────────────────────────────────
resource "aws_s3_bucket" "code" {
  bucket_prefix = "skynet-runtime-code-"
  force_destroy = true # rebuilt from the repo
  tags          = { Name = "skynet-runtime-code" }
}

resource "aws_s3_bucket_public_access_block" "code" {
  bucket                  = aws_s3_bucket.code.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_object" "code" {
  bucket      = aws_s3_bucket.code.id
  key         = "skynet_hunt/runtime-${filemd5(local.zip)}.zip" # a new key per build, so the runtime redeploys
  source      = local.zip
  source_hash = filemd5(local.zip)
  tags        = { Name = "skynet-runtime-zip" }

  lifecycle {
    precondition {
      condition     = fileexists(local.zip)
      error_message = "Run ./infra/runtime/build_runtime.sh first."
    }
  }
}

# ── execution role ───────────────────────────────────────────────────────────
data "aws_iam_policy_document" "trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["bedrock-agentcore.amazonaws.com"]
    }
    condition { # confused-deputy guard: only runtimes in this account
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.account]
    }
    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:${local.part}:bedrock-agentcore:${var.region}:${local.account}:*"]
    }
  }
}

resource "aws_iam_role" "runtime" {
  name_prefix        = "skynet-runtime-"
  assume_role_policy = data.aws_iam_policy_document.trust.json
  tags               = { Name = "skynet-runtime-exec" }
}

data "aws_iam_policy_document" "runtime" {
  statement {
    sid       = "Models"
    actions   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
    resources = concat(local.profile_arns, local.model_arns)
  }
  statement {
    sid       = "Archive"
    actions   = ["bedrock:Retrieve"]
    resources = ["arn:${local.part}:bedrock:${var.region}:${local.account}:knowledge-base/${local.kb_id}"]
  }
  statement {
    sid     = "Gate"
    actions = ["bedrock:ApplyGuardrail"]
    resources = [
      "arn:${local.part}:bedrock:${var.region}:${local.account}:guardrail/${local.guardrail[0]}",
      "arn:${local.part}:bedrock:*:${local.account}:guardrail-profile/${var.guardrail_profile}",
    ]
  }
  statement {
    sid       = "Code"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.code.arn}/*"]
  }
  statement {
    sid       = "Logs"
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogStreams", "logs:DescribeLogGroups"]
    resources = ["arn:${local.part}:logs:${var.region}:${local.account}:log-group:/aws/bedrock-agentcore/runtimes/*"]
  }
  statement {
    sid       = "Metrics"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "cloudwatch:namespace"
      values   = ["bedrock-agentcore"]
    }
  }
  statement {
    sid       = "WorkloadIdentity"
    actions   = ["bedrock-agentcore:GetWorkloadAccessToken", "bedrock-agentcore:GetWorkloadAccessTokenForJWT"]
    resources = ["arn:${local.part}:bedrock-agentcore:${var.region}:${local.account}:workload-identity-directory/default*"]
  }
}

resource "aws_iam_role_policy" "runtime" {
  role   = aws_iam_role.runtime.id
  policy = data.aws_iam_policy_document.runtime.json
}

# ── runtime ──────────────────────────────────────────────────────────────────
resource "aws_bedrockagentcore_agent_runtime" "hunt" {
  agent_runtime_name = "skynet_hunt" # letters, digits, underscores: AWS shows this name as-is
  description        = "Skynet Hunter: the hunt on AgentCore Runtime, models on Bedrock, archive via KB + guardrail."
  role_arn           = aws_iam_role.runtime.arn

  agent_runtime_artifact {
    code_configuration {
      entry_point = ["main.py"]
      runtime     = "PYTHON_3_13"
      code {
        s3 {
          bucket = aws_s3_bucket.code.id
          prefix = aws_s3_object.code.key
        }
      }
    }
  }

  network_configuration { network_mode = "PUBLIC" }

  lifecycle_configuration {
    idle_runtime_session_timeout = var.idle_timeout_s # compute stops billing this long after the last call
    max_lifetime                 = var.max_lifetime_s
  }

  environment_variables = {
    SKYNET_REGION     = var.region
    KB_ID             = local.kb_id
    GUARDRAIL_ID      = local.guardrail[0]
    GUARDRAIL_VERSION = local.guardrail[1]
    MIN_SCORE         = "0.60"
  }

  tags = { Name = "skynet-hunt-runtime" }

  depends_on = [aws_iam_role_policy.runtime]
}
