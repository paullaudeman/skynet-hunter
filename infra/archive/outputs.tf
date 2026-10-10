output "knowledge_base_id" { value = aws_bedrockagent_knowledge_base.archive.id }
output "guardrail" { value = "${aws_bedrock_guardrail.archive.guardrail_id}:${aws_bedrock_guardrail_version.v2.version}" }
output "gateway_url" { value = aws_bedrockagentcore_gateway.archive.gateway_url }
output "run_locally" {
  value = "uv run python -m skynet --archive-kb ${aws_bedrockagent_knowledge_base.archive.id} --guardrail ${aws_bedrock_guardrail.archive.guardrail_id}:${aws_bedrock_guardrail_version.v2.version} --aws-region ${var.region}"
}
output "log_group" { value = aws_cloudwatch_log_group.archive.name }
