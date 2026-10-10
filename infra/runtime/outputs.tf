output "agent_runtime_arn" { value = aws_bedrockagentcore_agent_runtime.hunt.agent_runtime_arn }
output "run" {
  value = "uv run python -m skynet --runtime ${aws_bedrockagentcore_agent_runtime.hunt.agent_runtime_arn} --aws-region ${var.region}"
}
output "log_group_prefix" { value = "/aws/bedrock-agentcore/runtimes/${aws_bedrockagentcore_agent_runtime.hunt.agent_runtime_id}" }
